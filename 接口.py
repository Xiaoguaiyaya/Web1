from flask import Flask, request, jsonify,g
import pymysql
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins="*")
CORS(app, supports_credentials=True)
# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'webshixi',
    'cursorclass': pymysql.cursors.DictCursor
}
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost/webshixi'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 60  # 设置为 60 秒


# 在请求之前创建数据库连接
@app.before_request
def before_request():
    g.connection = pymysql.connect(**db_config)

# 在请求结束时关闭数据库连接
@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'connection'):
        g.connection.close()

# 登录请求
@app.route('/login', methods=['POST']) #已用
def login():
    data = request.get_json()

    if 'username' not in data or 'password' not in data:
        return jsonify({'error': '缺少用户名或密码'}), 400

    username = data['username']
    password = data['password']

    # 执行 SQL 查询
    with g.connection.cursor() as cursor:
        query = "SELECT * FROM tb_user WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

    if user and user['password'] == password:
        return jsonify({'status': '200', 'user_id': user['id'], 'identity': user['identity']}), 200
    else:
        return jsonify({'status': '401', 'error': '无效的用户名或密码'})

# 注册请求
@app.route('/register', methods=['POST']) #已用
def register():
    data = request.get_json()

    # 在检查用户名存在的基础上，添加对用户名、密码和身份非空的检查
    if 'username' not in data or 'password' not in data or 'identity' not in data \
            or not data['username'] or not data['password'] or not data['identity']:
        return jsonify({'status': '400', 'error': '缺少用户名、密码或身份，或用户名/密码/身份为空'}), 400

    username = data['username']
    password = data['password']
    identity = data['identity']

    # 检查用户名是否已经存在
    with g.connection.cursor() as cursor:
        query = "SELECT * FROM tb_user WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({'status': '400', 'error': '用户名已经存在'}), 400

    # 插入新用户
    with g.connection.cursor() as cursor:
        query = "INSERT INTO tb_user (username, password, identity) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, identity))
        new_user_id = cursor.lastrowid

    g.connection.commit()
    return jsonify({'status': '200', 'user_id': new_user_id}), 200

# 更新密码请求
@app.route('/update_password', methods=['POST'])
def update_password():
    data = request.get_json()

    if 'user_id' not in data or 'password' not in data:
        return jsonify({'error': '缺少user_id或password'}), 400

    user_id = data['user_id']
    password = data['password']

    try:
        with g.connection.cursor() as cursor:
            # 更新用户密码
            update_password_query = "UPDATE tb_user SET password=%s WHERE id=%s"
            cursor.execute(update_password_query, (password, user_id))
            g.connection.commit()

            return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 删除用户请求
@app.route('/delete_user', methods=['POST']) #已用
def delete_user():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': '缺少user_id'}), 400

    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 删除与用户关联的点击率记录
            delete_clickthroughrate_query = "DELETE FROM clickthroughrate WHERE user_id = %s"
            cursor.execute(delete_clickthroughrate_query, (user_id,))

            # 删除与用户关联的收藏记录
            delete_collect_query = "DELETE FROM collect WHERE user_id = %s"
            cursor.execute(delete_collect_query, (user_id,))

            # 删除与用户关联的评论回复记录
            delete_comment_reply_query = "DELETE FROM comment_reply WHERE user_id = %s"
            cursor.execute(delete_comment_reply_query, (user_id,))

            # 删除与用户关联的评论记录
            delete_comment_query = "DELETE FROM comment WHERE user_id = %s"
            cursor.execute(delete_comment_query, (user_id,))

            # 删除与用户关联的附件记录
            delete_annex_query = "DELETE FROM annex WHERE user_id = %s"
            cursor.execute(delete_annex_query, (user_id,))

            # 删除与用户关联的博客记录
            delete_blog_query = "DELETE FROM blog WHERE user_id = %s"
            cursor.execute(delete_blog_query, (user_id,))

            # 删除与用户关联的用户积分记录
            delete_user_integral_query = "DELETE FROM user_integral WHERE user_id = %s"
            cursor.execute(delete_user_integral_query, (user_id,))

            # 删除关注表中关注了该用户的记录
            delete_concern_query = "DELETE FROM concern WHERE user_id_2 = %s"
            cursor.execute(delete_concern_query, (user_id,))

            # 最后删除用户
            delete_user_query = "DELETE FROM tb_user WHERE id = %s"
            cursor.execute(delete_user_query, (user_id,))

            g.connection.commit()

            return jsonify({'status':'200','success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# 更新用户信息的路由
@app.route('/update_user', methods=['POST']) #已用
def update_user():
    data = request.get_json()

    if 'id' not in data:
        return jsonify({'error': '缺少用户ID'}), 400

    user_id = data['id']
    new_username = data.get('username')
    new_password = data.get('password')
    new_identity = data.get('identity')

    try:
        with pymysql.connect(**db_config) as connection, connection.cursor() as cursor:
            # 构建更新用户信息的SQL语句
            update_query = "UPDATE tb_user SET"
            update_values = []

            if new_username is not None:
                update_query += " username = %s,"
                update_values.append(new_username)

            if new_password is not None:
                update_query += " password = %s,"
                update_values.append(new_password)

            if new_identity is not None:
                update_query += " identity = %s,"
                update_values.append(new_identity)

            # 移除最后一个逗号
            update_query = update_query.rstrip(',')

            update_query += " WHERE id = %s"
            update_values.append(user_id)

            # 执行更新操作
            cursor.execute(update_query, tuple(update_values))
            connection.commit()

            return jsonify({'status': '200', 'message': '用户信息更新成功'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 用户存在性检查的接口
@app.route('/check_user', methods=['POST']) #已用
def check_user():
    data = request.get_json()

    if 'username' not in data:
        return jsonify({'error': '缺少用户名'}), 400

    username = data['username']

    try:
        with g.connection.cursor() as cursor:
            # 查询用户是否存在
            query = "SELECT id FROM tb_user WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

        if user:
            return jsonify({'status': '200', 'message': '用户存在'})
        else:
            return jsonify({'status': '401', 'error': '用户不存在'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 查看所有用户的接口
@app.route('/get_all_users', methods=['GET']) #已用
def get_all_users():
    with g.connection.cursor() as cursor:
        # 查询所有用户信息
        query = "SELECT id, username, password, identity FROM tb_user"
        cursor.execute(query)
        users = cursor.fetchall()
    print(users)
    return jsonify({'success': True, 'users': users}), 200

# 模糊查看用户的接口
@app.route('/get_like_users', methods=['POST']) #已用
def get_like_users():
    data = request.get_json()

    search_keyword = data['search']
    try:
        with g.connection.cursor() as cursor:

            search_keyword = '%' + search_keyword + '%'
            query = """
                SELECT id, username, password, identity 
                FROM tb_user 
                WHERE 
                    id LIKE %s OR
                    username LIKE %s OR
                    identity LIKE %s
            """
            cursor.execute(query, (search_keyword, search_keyword, search_keyword))

            users = cursor.fetchall()

        return jsonify({'success': True, 'users': users}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取用户详情的接口
@app.route('/user-details-h', methods=['POST'])
def get_user_details():
    data = request.get_json()

    user_id = data['user_id']
    print(user_id)
    with g.connection.cursor() as cursor:
        query = """SELECT
        u.id AS user_id,
        u.username,
        u.password,
        u.identity,
        COUNT(DISTINCT b.id) AS article_count,
        COUNT(DISTINCT c.id) AS comment_count,
        COUNT(DISTINCT c1.id) AS following_count,
        COUNT(DISTINCT c2.id) AS followers_count,
        COUNT(DISTINCT a.id) AS attachment_count
        FROM tb_user u
        LEFT JOIN blog b ON u.id = b.user_id
        LEFT JOIN comment c ON u.id = c.user_id
        LEFT JOIN concern c1 ON u.id = c1.user_id_1
        LEFT JOIN concern c2 ON u.id = c2.user_id_2
        LEFT JOIN annex a ON u.id = a.user_id
        WHERE u.id = %s
        GROUP BY u.id, u.username, u.password, u.identity;
          -- 这里添加了 GROUP BY 子句，以便汇总用户信息
        """
        # 执行查询
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        if user:
            # 将查询结果组装成字典
            user_details = {
                'user_id': user['user_id'],
                'username': user['username'],
                'identity': user['identity'],
                'article_count': user['article_count'],
                'comment_count': user['comment_count'],
                'following_count': user['following_count'],
                'followers_count': user['followers_count'],
                'attachment_count': user['attachment_count'],
            }
            # 返回查询结果
            return jsonify({'status': 200, 'user': user_details}), 200
        else:
            # 用户不存在的情况下返回错误信息
            return jsonify({'status': 404, 'error': '用户不存在'}), 404

# 删除文章请求
@app.route('/delete_blog', methods=['POST']) #已用
def delete_blog():
    data = request.get_json()

    if 'blog_id' not in data:
        return jsonify({'error': '缺少blog_id'}), 400

    blog_id = data['blog_id']

    try:
        with g.connection.cursor() as cursor:
            # 删除评论表中与该文章相关的评论
            delete_comments_query = "DELETE FROM comment WHERE blog_id = %s"
            cursor.execute(delete_comments_query, (blog_id,))

            # 删除回复评论表中与该文章相关的回复评论
            delete_comment_replies_query = "DELETE FROM comment_reply WHERE blog_id = %s"
            cursor.execute(delete_comment_replies_query, (blog_id,))

            # 删除附件表中与该文章相关的附件
            delete_annex_query = "DELETE FROM annex WHERE blog_id = %s"
            cursor.execute(delete_annex_query, (blog_id,))

            # 删除点击率表中与该文章相关的点击率
            delete_clickthroughrate_query = "DELETE FROM clickthroughrate WHERE blog_id = %s"
            cursor.execute(delete_clickthroughrate_query, (blog_id,))

            # 删除收藏表中与该文章相关的收藏
            delete_collect_query = "DELETE FROM collect WHERE blog_id = %s"
            cursor.execute(delete_collect_query, (blog_id,))

            # 最后删除文章本身
            delete_blog_query = "DELETE FROM blog WHERE id = %s"
            cursor.execute(delete_blog_query, (blog_id,))

            g.connection.commit()

            return jsonify({'status': 200, 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 读取文章请求
@app.route('/read_article', methods=['POST'])
def read_article():
    data = request.get_json()

    if 'title1' not in data or 'title2' not in data:
        return jsonify({'error': '缺少文章标题'}), 400

    title1 = data['title1']
    title2 = data['title2']

    # 查询文章信息
    with g.connection.cursor() as cursor:
        query = "SELECT id, title, creat_time FROM blog WHERE title1 = %s AND title2 = %s"
        cursor.execute(query, (title1, title2))
        articles = cursor.fetchall()

    if articles:
        return jsonify({'success': True, 'articles': articles}), 200
    else:
        return jsonify({'error': '找不到指定的文章'}), 404


# 最新15文章请求
@app.route('/latest_articles', methods=['GET'])
def latest_articles():
    # 查询最新时间的前15篇文章信息
    with g.connection.cursor() as cursor:
        query = "SELECT title, creat_time FROM blog ORDER BY creat_time DESC LIMIT 15"
        cursor.execute(query)
        articles = cursor.fetchall()

    if articles:
        return jsonify(articles), 200
    else:
        return jsonify({'error': '找不到文章'}), 404

# 获取文章列表的路由，获取全部文章
@app.route('/get_articles', methods=['GET']) #已用
def get_articles():
    try:
        with g.connection.cursor() as cursor:
            query = "SELECT blog.id AS article_id, title1, title2, title, username AS author, creat_time FROM blog JOIN tb_user ON blog.user_id = tb_user.id"
            cursor.execute(query)

            # 获取所有文章信息
            articles = cursor.fetchall()
            print(articles)
        return jsonify({'status': '200', 'articles': articles}), 200

    except Exception as e:
        return jsonify({'status': '500', 'error': str(e)}), 500

# 模糊搜索文章请求
@app.route('/get_like_articles', methods=['POST']) #已用
def get_like_articles():
    data = request.get_json()

    if 'search' not in data:
        return jsonify({'status': '400', 'error': '缺少搜索关键字'}), 400

    search_keyword = data['search']

    with g.connection.cursor() as cursor:
        # 使用 JOIN 连接用户表和文章表，并使用 LIKE 运算符进行模糊搜索
        query = """
                SELECT b.id AS article_id, b.title1, b.title2, b.title, u.username AS author, b.creat_time
                FROM blog b
                JOIN tb_user u ON b.user_id = u.id
                WHERE b.title1 LIKE %s OR b.title2 LIKE %s OR b.title LIKE %s OR u.username LIKE %s OR b.text LIKE %s
                """
        cursor.execute(query, (
        f"%{search_keyword}%", f"%{search_keyword}%", f"%{search_keyword}%", f"%{search_keyword}%",
        f"%{search_keyword}%"))
        articles = cursor.fetchall()


    if articles:
        return jsonify({'status': '200', 'articles': articles}), 200
    else:
        return jsonify({'status': '404', 'error': '找不到指定的文章'}), 404

# 查询用户
@app.route('/get_user', methods=['POST'])
def get_user():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'status': '400', 'error': '缺少用户ID'}), 400

    user_id = data['user_id']

    # 查询用户信息
    with g.connection.cursor() as cursor:
        query = "SELECT id, username FROM tb_user WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

    if user:
        return jsonify({'status': '200', 'username': user['username']}), 200
    else:
        return jsonify({'status': '404', 'error': '找不到指定的用户'}), 404
