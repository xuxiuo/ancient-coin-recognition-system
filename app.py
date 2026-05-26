"""
古钱币识别系统 - Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import shutil
from datetime import datetime
from predict import get_predictor
from coin_info import get_coin_info

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大50MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# 创建必要的文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# 初始化预测器
predictor = None

def delete_temp_files(paths):
    """删除临时上传文件，忽略错误"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"删除临时文件失败 {path}: {e}")

def init_predictor():
    """初始化预测器"""
    global predictor
    if predictor is None:
        try:
            predictor = get_predictor()
            print("✅ 预测器初始化成功")
        except Exception as e:
            print(f"❌ 预测器初始化失败: {e}")
            raise
    return predictor

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_classified_image(image_path, class_name, result_folder):
    """将识别后的图片按类别分类保存"""
    try:
        # 创建类别文件夹
        class_folder = os.path.join(result_folder, class_name)
        os.makedirs(class_folder, exist_ok=True)
        
        # 生成新的文件名（时间戳+原文件名）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = os.path.basename(image_path)
        name, ext = os.path.splitext(original_name)
        new_filename = f"{timestamp}_{name}{ext}"
        
        # 复制文件到类别文件夹
        dest_path = os.path.join(class_folder, new_filename)
        shutil.copy2(image_path, dest_path)
        
        return dest_path
    except Exception as e:
        print(f"保存分类文件失败: {e}")
        return None

@app.route('/')
def intro():
    """默认进入系统介绍页"""
    return render_template('intro.html')

@app.route('/intro')
def intro_alias():
    """系统介绍页别名"""
    return render_template('intro.html')

@app.route('/index')
def index():
    """主页（识别页面）"""
    return render_template('index.html')

@app.route('/api/check_image', methods=['POST'])
def check_image():
    """单张图片方向校验：expected_side = obverse/reverse"""
    try:
        if 'image' not in request.files or 'expected_side' not in request.form:
            return jsonify({'success': False, 'error': '缺少文件或参数'}), 400
        img_file = request.files['image']
        expected = request.form['expected_side']
        if img_file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        if not allowed_file(img_file.filename):
            return jsonify({'success': False, 'error': '不支持的文件格式'}), 400

        # 保存临时文件
        temp_name = secure_filename(img_file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"check_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{temp_name}")
        img_file.save(temp_path)

        pred = init_predictor()
        try:
            result = pred.predict(temp_path, top_k=1)
            class_name, confidence = result[0]
            info = get_coin_info(class_name)
            side = info.get("side", "未知")
        except Exception as e:
            delete_temp_files([temp_path])
            return jsonify({'success': False, 'error': f'识别失败: {e}'}), 200

        delete_temp_files([temp_path])

        # 预判：正面期望“正面”，反面期望“反面”
        if expected == 'obverse' and side == '反面':
            return jsonify({'success': False, 'match': False, 'side': side, 'class_name': class_name, 'confidence': confidence, 'message': '正面上传的似乎是反面，请重新上传正面。'}), 200
        if expected == 'reverse' and side == '正面':
            return jsonify({'success': False, 'match': False, 'side': side, 'class_name': class_name, 'confidence': confidence, 'message': '反面上传的似乎是正面，请重新上传反面。'}), 200

        return jsonify({'success': True, 'match': True, 'side': side, 'class_name': class_name, 'confidence': confidence}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/single_predict', methods=['POST'])
def single_predict():
    """单币识别API（上传正反面两张图片）"""
    try:
        # 检查文件
        if 'obverse' not in request.files or 'reverse' not in request.files:
            return jsonify({'error': '请上传正反面两张图片'}), 400
        
        obverse_file = request.files['obverse']
        reverse_file = request.files['reverse']
        
        if obverse_file.filename == '' or reverse_file.filename == '':
            return jsonify({'error': '请选择文件'}), 400
        
        if not (allowed_file(obverse_file.filename) and allowed_file(reverse_file.filename)):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 初始化预测器
        pred = init_predictor()
        
        # 保存上传的文件
        obverse_filename = secure_filename(obverse_file.filename)
        reverse_filename = secure_filename(reverse_file.filename)
        
        obverse_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                   f"obverse_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{obverse_filename}")
        reverse_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                   f"reverse_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{reverse_filename}")
        
        obverse_file.save(obverse_path)
        reverse_file.save(reverse_path)
        
        # 提取币种名称的函数
        def extract_coin_name(class_name):
            """从类别名称中提取币种名称（去掉_正、_反等后缀）"""
            # 处理各种可能的命名格式
            name = class_name.replace("！", "").replace("!", "")
            if "_正" in name or "_反" in name or "-正" in name or "-反" in name:
                # 找到最后一个_或-的位置
                for sep in ["_正", "_反", "-正", "-反"]:
                    if sep in name:
                        return name.split(sep)[0]
            return name
        
        # 预测（处理识别失败的情况）
        obverse_success = True
        reverse_success = True
        obverse_result = None
        reverse_result = None
        obverse_error = None
        reverse_error = None
        
        try:
            obverse_result = pred.predict(obverse_path, top_k=3)
        except Exception as e:
            obverse_success = False
            obverse_error = str(e)
        
        try:
            reverse_result = pred.predict(reverse_path, top_k=3)
        except Exception as e:
            reverse_success = False
            reverse_error = str(e)
        
        # 如果都识别失败
        if not obverse_success and not reverse_success:
            # 删除临时文件
            delete_temp_files([obverse_path, reverse_path])
            return jsonify({
                'success': False,
                'match_status': 'both_failed',
                'obverse_error': obverse_error,
                'reverse_error': reverse_error
            }), 200
        
        # 如果只有一个识别失败
        if not obverse_success:
            # 保存成功的反面文件
            save_classified_image(reverse_path, reverse_result[0][0], app.config['RESULT_FOLDER'])
            # 删除临时文件
            delete_temp_files([obverse_path, reverse_path])
            return jsonify({
                'success': False,
                'match_status': 'obverse_failed',
                'reverse': {
                    'class_name': reverse_result[0][0],
                    'confidence': reverse_result[0][1],
                    'top_predictions': [{'class': c, 'confidence': conf} for c, conf in reverse_result],
                    'info': get_coin_info(reverse_result[0][0])
                },
                'obverse_error': obverse_error
            }), 200
        
        if not reverse_success:
            # 保存成功的正面文件
            save_classified_image(obverse_path, obverse_result[0][0], app.config['RESULT_FOLDER'])
            # 删除临时文件
            delete_temp_files([obverse_path, reverse_path])
            return jsonify({
                'success': False,
                'match_status': 'reverse_failed',
                'obverse': {
                    'class_name': obverse_result[0][0],
                    'confidence': obverse_result[0][1],
                    'top_predictions': [{'class': c, 'confidence': conf} for c, conf in obverse_result],
                    'info': get_coin_info(obverse_result[0][0])
                },
                'reverse_error': reverse_error
            }), 200
        
        # 两个都识别成功，判断是否匹配
        obverse_class = obverse_result[0][0]
        reverse_class = reverse_result[0][0]
        
        obverse_coin_name = extract_coin_name(obverse_class)
        reverse_coin_name = extract_coin_name(reverse_class)
        
        obverse_info = get_coin_info(obverse_class)
        reverse_info = get_coin_info(reverse_class)

        # 正反面方向校验
        if obverse_info.get("side") == "反面":
            delete_temp_files([obverse_path, reverse_path])
            return jsonify({
                'success': False,
                'match_status': 'obverse_wrong_side',
                'error': '正面上传的似乎是反面图片，请重新上传正确的正面。',
                'detail': obverse_class
            }), 200
        if reverse_info.get("side") == "正面":
            delete_temp_files([obverse_path, reverse_path])
            return jsonify({
                'success': False,
                'match_status': 'reverse_wrong_side',
                'error': '反面上传的似乎是正面图片，请重新上传正确的反面。',
                'detail': reverse_class
            }), 200
        
        # 判断是否匹配
        is_matched = (obverse_coin_name == reverse_coin_name)
        
        # 保存分类文件
        save_classified_image(obverse_path, obverse_class, app.config['RESULT_FOLDER'])
        save_classified_image(reverse_path, reverse_class, app.config['RESULT_FOLDER'])
        
        # 删除临时文件（识别完成后）
        delete_temp_files([obverse_path, reverse_path])
        
        # 构建返回结果
        if is_matched:
            # 匹配：使用置信度更高的结果
            if obverse_result[0][1] >= reverse_result[0][1]:
                main_class = obverse_class
                main_result = obverse_result
            else:
                main_class = reverse_class
                main_result = reverse_result
            
            result = {
                'success': True,
                'match_status': 'matched',
                'coin_name': obverse_coin_name,
                'class_name': main_class,
                'confidence': main_result[0][1],
                'top_predictions': [{'class': c, 'confidence': conf} for c, conf in main_result],
                'info': get_coin_info(main_class),
                'obverse': {
                    'class_name': obverse_class,
                    'confidence': obverse_result[0][1],
                    'info': obverse_info
                },
                'reverse': {
                    'class_name': reverse_class,
                    'confidence': reverse_result[0][1],
                    'info': reverse_info
                }
            }
        else:
            # 不匹配：分别输出
            result = {
                'success': True,
                'match_status': 'not_matched',
                'obverse': {
                    'class_name': obverse_class,
                    'coin_name': obverse_coin_name,
                    'confidence': obverse_result[0][1],
                    'top_predictions': [{'class': c, 'confidence': conf} for c, conf in obverse_result],
                    'info': obverse_info
                },
                'reverse': {
                    'class_name': reverse_class,
                    'coin_name': reverse_coin_name,
                    'confidence': reverse_result[0][1],
                    'top_predictions': [{'class': c, 'confidence': conf} for c, conf in reverse_result],
                    'info': reverse_info
                }
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'识别失败: {str(e)}'}), 500

@app.route('/api/batch_predict', methods=['POST'])
def batch_predict():
    """多币识别API（批量上传最多50张图片）"""
    try:
        # 检查文件
        if 'images' not in request.files:
            return jsonify({'error': '请上传图片'}), 400
        
        files = request.files.getlist('images')
        
        if len(files) == 0:
            return jsonify({'error': '请选择文件'}), 400
        
        # 处理超过50个文件的情况
        total_files = len(files)
        files_to_process = files[:50]  # 只处理前50个
        exceeded_count = total_files - 50 if total_files > 50 else 0
        
        # 过滤有效文件（只处理前50个）
        valid_files = []
        for file in files_to_process:
            if file.filename != '' and allowed_file(file.filename):
                valid_files.append(file)
        
        if len(valid_files) == 0:
            return jsonify({'error': '没有有效的图片文件'}), 400
        
        # 初始化预测器
        pred = init_predictor()
        
        # 保存并预测
        results = []
        image_paths = []
        file_mapping = {}  # 保存文件路径到原始文件名的映射
        
        for file in valid_files:
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # 添加微秒避免重名
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                    f"{timestamp}_{original_filename}")
            file.save(file_path)
            image_paths.append(file_path)
            file_mapping[file_path] = original_filename
        
        # 批量预测
        batch_results = pred.predict_batch(image_paths, top_k=3)
        
        # 提取币种名称的函数
        def extract_coin_name(class_name):
            """从类别名称中提取币种名称（去掉_正、_反等后缀）"""
            name = class_name.replace("！", "").replace("!", "")
            if "_正" in name or "_反" in name or "-正" in name or "-反" in name:
                for sep in ["_正", "_反", "-正", "-反"]:
                    if sep in name:
                        return name.split(sep)[0]
            return name
        
        # 按币种分组处理结果
        coin_groups = {}  # {coin_name: [results]}
        failed_results = []  # 识别失败的图片
        
        for i, result in enumerate(batch_results):
            if result['success']:
                class_name = result['predictions'][0][0]
                confidence = result['predictions'][0][1]
                coin_name = extract_coin_name(class_name)
                coin_info = get_coin_info(class_name)
                
                # 保存分类文件
                save_classified_image(result['image_path'], class_name, app.config['RESULT_FOLDER'])
                
                # 获取原始文件名
                original_filename = file_mapping.get(result['image_path'], os.path.basename(result['image_path']))
                
                # 读取图片的base64用于前端显示
                import base64
                try:
                    with open(result['image_path'], 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                        image_ext = os.path.splitext(result['image_path'])[1].lower()
                        # 确定MIME类型
                        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', 
                                   '.gif': 'image/gif', '.bmp': 'image/bmp'}
                        image_mime = mime_map.get(image_ext, 'image/jpeg')
                        image_base64 = f"data:{image_mime};base64,{image_data}"
                except Exception as e:
                    print(f"读取图片失败: {e}")
                    image_base64 = ""  # 如果读取失败，使用空字符串
                
                item = {
                    'filename': original_filename,
                    'class_name': class_name,
                    'coin_name': coin_name,
                    'confidence': confidence,
                    'top_predictions': [{'class': c, 'confidence': conf} 
                                      for c, conf in result['predictions']],
                    'info': coin_info,
                    'image_path': result['image_path'],
                    'image_base64': image_base64
                }
                
                # 按币种分组
                if coin_name not in coin_groups:
                    coin_groups[coin_name] = {
                        'coin_name': coin_name,
                        'info': coin_info,
                        'items': []
                    }
                coin_groups[coin_name]['items'].append(item)
            else:
                original_filename = file_mapping.get(result['image_path'], os.path.basename(result['image_path']))
                failed_results.append({
                    'filename': original_filename,
                    'error': result.get('error', '识别失败'),
                    'success': False
                })
        
        # 将分组结果转换为列表
        grouped_results = list(coin_groups.values())
        
        # 删除所有临时文件（识别完成后）
        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"删除临时文件失败 {image_path}: {e}")
        
        return jsonify({
            'success': True,
            'total': len(batch_results),
            'total_uploaded': total_files,
            'processed': len(valid_files),
            'exceeded_count': exceeded_count,
            'grouped_results': grouped_results,
            'failed_results': failed_results
        })
        
    except Exception as e:
        return jsonify({'error': f'批量识别失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    try:
        pred = init_predictor()
        return jsonify({
            'status': 'healthy',
            'model_loaded': True,
            'num_classes': len(pred.class_to_idx)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'model_loaded': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("正在初始化预测器...")
    try:
        init_predictor()
        print("✅ 系统准备就绪！")
        print("访问 http://127.0.0.1:5000 使用古钱币识别系统")
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        print("请检查模型文件是否存在")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

