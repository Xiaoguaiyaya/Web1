import os
from datetime import datetime

from flask import Flask, request, jsonify, g, send_file, send_from_directory, render_template
import pymysql
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
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
app.config['SQLALCHEMY_POOL_RECYCLE'] = 60

# 设置文件上传路径
UPLOAD_FOLDER = 'file_annex'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
@app.route('/login', methods=['POST'])  # 已用
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
@app.route('/register', methods=['POST'])  # 已用
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
@app.route('/delete_user', methods=['POST'])  # 已用
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

            return jsonify({'status': '200', 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 更新用户信息的路由
@app.route('/update_user', methods=['POST'])  # 已用
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
@app.route('/check_user', methods=['POST'])  # 已用
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
@app.route('/get_all_users', methods=['GET'])  # 已用
def get_all_users():
    with g.connection.cursor() as cursor:
        # 查询所有用户信息
        query = "SELECT id, username, password, identity FROM tb_user"
        cursor.execute(query)
        users = cursor.fetchall()
    print(users)
    return jsonify({'success': True, 'users': users}), 200


# 模糊查看用户的接口
@app.route('/get_like_users', methods=['POST'])  # 已用
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

# 发布文章的接口
@app.route('/publish_article', methods=['POST'])
def publish_article():
    data = request.get_json()

    title1 = data['title1']
    title2 = data['title2']
    title = data['title3']
    user_id = data['user_id']
    create_time = data['create_time']
    text = data['text']
    annex_route = data['annex_route']


    with g.connection.cursor() as cursor:
        # 插入数据到文章表
        insert_blog_query = "INSERT INTO blog (title1, title2, title, user_id, creat_time, text) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_blog_query, (title1, title2, title, user_id, create_time, text))
        g.connection.commit()
        if annex_route=='None':
            return jsonify({'success': True}), 200
        else:
            # 获取插入的文章的ID
            blog_id = cursor.lastrowid
            # 插入数据到附件表
            insert_annex_query = "INSERT INTO annex (route, blog_id, user_id) VALUES (%s, %s, %s)"
            cursor.execute(insert_annex_query, (annex_route, blog_id, user_id))
            g.connection.commit()
            return jsonify({'success': True}), 200


# 更新文章请求
@app.route('/edit_blog', methods=['POST'])
def edit_blog():
    data = request.get_json()

    blog_id = data['blog_id']
    title1 = data['title1']
    title2 = data['title2']
    creat_time = data['creat_time']
    user_id = data['user_id']
    text = data['text']
    title = data['title']
    annex_route = data['annex_route']


    with g.connection.cursor() as cursor:
        # 更新文章信息
        update_query = "UPDATE blog SET title1=%s, title2=%s, creat_time=%s, user_id=%s, text=%s, title=%s WHERE id=%s"
        cursor.execute(update_query, (title1, title2, creat_time, user_id, text, title, blog_id))
        g.connection.commit()
        if annex_route == 'None':
            return jsonify({'success': True}), 200
        else:
            # 获取插入的文章的ID
            blog_id = cursor.lastrowid
            # 插入数据到附件表
            insert_annex_query = "INSERT INTO annex (route, blog_id, user_id) VALUES (%s, %s, %s)"
            cursor.execute(insert_annex_query, (annex_route, blog_id, user_id))
            g.connection.commit()
            return jsonify({'success': True}), 200




# 删除文章请求
@app.route('/delete_blog', methods=['POST'])  # 已用
def delete_blog():
    data = request.get_json()

    if 'blog_id' not in data:
        return jsonify({'error': '缺少blog_id'}), 400

    blog_id = data['blog_id']

    try:
        with g.connection.cursor() as cursor:
            # 删除回复评论表中与该文章相关的回复评论
            delete_comment_replies_query = "DELETE FROM comment_reply WHERE comment_id IN (SELECT id FROM comment WHERE blog_id = %s)"
            cursor.execute(delete_comment_replies_query, (blog_id,))

            # 删除评论表中与该文章相关的评论
            delete_comments_query = "DELETE FROM comment WHERE blog_id = %s"
            cursor.execute(delete_comments_query, (blog_id,))

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

# 读取文章请求
@app.route('/read_article_f', methods=['POST'])
def read_article_f():
    data = request.json

    if 'title1' not in data or 'title2' not in data:
        return jsonify({'error': '缺少文章标题'}), 400

    title1 = data['title1']
    title2 = data['title2']

    # 分页参数
    page = data.get('page', 1)
    page = int(page)
    page_size = data.get('pageSize', 10)
    page_size = int(page_size)
    # 根据页数和每页大小计算偏移量
    offset = (page - 1) * page_size

    # 查询分页文章
    with g.connection.cursor() as cursor:
        query = "SELECT id, title, creat_time FROM blog WHERE title1 = %s AND title2 = %s LIMIT %s OFFSET %s"
        cursor.execute(query, (title1, title2, page_size, offset))
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
@app.route('/get_articles', methods=['GET'])  # 已用
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

#获取指定用户文章
@app.route('/get_user_articles', methods=['POST'])
def get_user_articles():
    data = request.get_json()
    user_id = data.get('user_id')

    with g.connection.cursor() as cursor:
        query = """
            SELECT blog.id AS article_id, title1, title2, title, username AS author, creat_time
            FROM blog
            JOIN tb_user ON blog.user_id = tb_user.id
            WHERE tb_user.id = %s
        """
        cursor.execute(query, (user_id,))
        articles = cursor.fetchall()

    return jsonify(articles)

# 后台管理员模糊搜索文章请求
@app.route('/get_like_articles', methods=['POST'])  # 已用
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


# 前台模糊搜索文章请求(title1，title2)
@app.route('/search_articles_title', methods=['POST'])
def search_articles_title():
    data = request.get_json()

    keyword = data['keyword']
    title1 = data['title1']
    title2 = data['title2']
    with g.connection.cursor() as cursor:
        # 查询符合title1和title2条件的文章
        query1 = """
            SELECT id, title, creat_time
            FROM blog
            WHERE title1 = %s AND title2 = %s
        """
        cursor.execute(query1, (title1, title2))
        result1 = cursor.fetchall()
        # 如果没有符合条件的文章，返回404
        if not result1:
            return jsonify({'message': '没有查询到该文章', 'success': 404})
        # 在符合条件的文章中执行关键词模糊查询
        articles = []
        for article in result1:
            article_id = article['id']
            query2 = """
                SELECT id, title, creat_time
                FROM blog
                WHERE id = %s AND (title LIKE %s OR text LIKE %s)
            """
            cursor.execute(query2, (article_id, f"%{keyword}%", f"%{keyword}%"))
            result2 = cursor.fetchall()
            articles.extend(result2)
        if not articles:
            return jsonify({'message': '没有查询到该文章', 'success': 404})
        return jsonify({'success': True, 'articles': articles})


# 模糊查询文章(根据标题title)
@app.route('/search_articles', methods=['POST'])
def search_articles():
    # 获取前端传递的关键词
    data = request.get_json()
    keyword = data.get('keyword', '')

    with g.connection.cursor() as cursor:
        # 执行模糊查询
        sql = """
            SELECT id AS article_id, title, creat_time
            FROM blog
            WHERE title1 LIKE %s OR title2 LIKE %s OR title LIKE %s
        """
        cursor.execute(sql, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        result = cursor.fetchall()
        # 返回 JSON 数据
        return jsonify({'success': True, 'articles': result})

# 读取文章请求
@app.route('/read_article1', methods=['POST'])
def read_article1():
    data = request.get_json()

    article_id = data['article_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询文章基本信息
            query_article = "SELECT title1, title2, title, creat_time, text, user_id FROM blog WHERE id = %s"
            cursor.execute(query_article, (article_id,))
            article_info = cursor.fetchone()

            if not article_info:
                return jsonify({'error': '找不到指定的文章'}), 404

            # 查询点击率
            query_click = "SELECT SUM(click) AS total_click FROM clickthroughrate WHERE blog_id = %s"
            cursor.execute(query_click, (article_id,))
            click_result = cursor.fetchone()
            total_click = click_result['total_click'] if click_result['total_click'] else 0

            # 查询收藏量
            query_collect = "SELECT COUNT(*) AS total_collect FROM collect WHERE blog_id = %s"
            cursor.execute(query_collect, (article_id,))
            collect_result = cursor.fetchone()
            total_collect = collect_result['total_collect'] if collect_result['total_collect'] else 0

            # 查询作者
            query_author = "SELECT username FROM tb_user WHERE id = %s"
            cursor.execute(query_author, (article_info['user_id'],))
            author_result = cursor.fetchone()
            author = author_result['username'] if author_result else '未知作者'

            # 构建返回的 JSON 数据
            response_data = {
                'success': True,
                'title1': article_info['title1'],
                'title2': article_info['title2'],
                'title': article_info['title'],
                'create_time': article_info['creat_time'],
                'text': article_info['text'],
                'author': author,
                'total_click': total_click,
                'total_collect': total_collect
            }

            return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_article_comments', methods=['POST'])
def get_article_comments():
    data = request.get_json()

    if 'article_id' not in data:
        return jsonify({'error': '缺少文章ID'}), 400

    article_id = data['article_id']

    # 查询文章相关评论和回复
    with g.connection.cursor() as cursor:
        # 查询文章评论
        comments_query = """
        SELECT c.id AS comment_id, c.text AS comment_text, c.create_time AS comment_time,
               c.user_id AS commenter_id, u.username AS commenter_username
        FROM comment c
        JOIN tb_user u ON c.user_id = u.id
        WHERE c.blog_id = %s
        """
        cursor.execute(comments_query, (article_id,))
        comments = cursor.fetchall()

        # 查询每条评论的回复评论
        for comment in comments:
            reply_query = """
            SELECT cr.id AS reply_id, cr.text AS reply_text, cr.create_time AS reply_time,
                   cr.user_id AS replier_id, u.username AS replier_username
            FROM comment_reply cr
            JOIN tb_user u ON cr.user_id = u.id
            WHERE cr.blog_id = %s AND cr.comment_id = %s
            """
            cursor.execute(reply_query, (article_id, comment['comment_id']))
            comment['replies'] = cursor.fetchall()

    return jsonify({'success': True, 'comments': comments}), 200


# 路由来处理查询点击率前八的文章
@app.route('/get_eight_clicked_articles', methods=['GET'])
def get_eight_clicked_articles():
    try:
        with g.connection.cursor() as cursor:
            # 执行查询，合并相同文章的点击率
            sql = """
                SELECT b.id AS article_id, b.creat_time AS publish_time, b.title, SUM(c.click) AS total_click
                FROM blog b
                LEFT JOIN clickthroughrate c ON b.id = c.blog_id
                GROUP BY b.id, b.creat_time, b.title
                ORDER BY total_click DESC
                LIMIT 8;
            """
            cursor.execute(sql)
            result = cursor.fetchall()

            # 返回 JSON 数据
            return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 获取前八篇文章的收藏数量，并按收藏数量排序
@app.route('/top8_collected_articles', methods=['GET'])
def top8_collected_articles():
    try:
        connection = pymysql.connect(**db_config)

        with connection.cursor() as cursor:
            # 查询前八篇文章的收藏数量
            query = """
                SELECT b.id as article_id, b.creat_time, b.title, COUNT(c.id) as collect_count
                FROM blog b
                LEFT JOIN collect c ON b.id = c.blog_id
                GROUP BY b.id
                ORDER BY collect_count DESC
                LIMIT 8
            """
            cursor.execute(query)
            result = cursor.fetchall()

            return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)})


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


# 计算用户积分
@app.route('/calculate_integral', methods=['POST'])
def calculate_integral():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': '缺少用户id'}), 400

    user_id = int(data['user_id'])

    with g.connection.cursor() as cursor:
        # 查询用户是否存在积分记录
        query_check = "SELECT user_id FROM user_integral WHERE user_id = %s"
        cursor.execute(query_check, (user_id,))
        existing_user = cursor.fetchone()
        if existing_user:
            # 如果用户存在积分记录，更新积分
            query_update = """
                UPDATE user_integral
                SET integral = COALESCE((SELECT COUNT(blog.id) FROM tb_user
                                        LEFT JOIN blog ON tb_user.id = blog.user_id
                                        WHERE tb_user.id = %s), 0)
                WHERE user_id = %s;
            """
            cursor.execute(query_update, (user_id, user_id))
            g.connection.commit()
        else:
            # 如果用户不存在积分记录，插入积分记录
            query_insert = """
                INSERT INTO user_integral (integral, user_id)
                SELECT COALESCE(COUNT(blog.id), 0) AS integral, tb_user.id AS user_id
                FROM tb_user
                LEFT JOIN blog ON tb_user.id = blog.user_id
                WHERE tb_user.id = %s
                GROUP BY tb_user.id;
            """
            cursor.execute(query_insert, (user_id,))
            g.connection.commit()
        # 查询用户积分
        query_integral = "SELECT integral FROM user_integral WHERE user_id = %s"
        cursor.execute(query_integral, (user_id,))
        result = cursor.fetchone()
        if result:
            return jsonify({'success': True, 'integral': result['integral']}), 200
        else:
            return jsonify({'error': '找不到用户积分'}), 404


# 更新点击率
@app.route('/update_clickthroughrate', methods=['POST'])
def update_clickthroughrate():
    data = request.get_json()

    if 'blog_id' not in data or 'user_id' not in data:
        return jsonify({'error': '缺少blog_id或user_id'}), 400

    blog_id = data['blog_id']
    user_id = data['user_id']
    click_value = data.get('click', 1)

    try:
        with g.connection.cursor() as cursor:
            # 检查表中是否已存在对应的行
            query = "SELECT * FROM clickthroughrate WHERE blog_id = %s AND user_id = %s"
            cursor.execute(query, (blog_id, user_id))
            existing_row = cursor.fetchone()

            if existing_row:
                # 如果已存在，则将click列的值加1
                update_query = "UPDATE clickthroughrate SET click = click + %s WHERE blog_id = %s AND user_id = %s"
                cursor.execute(update_query, (click_value, blog_id, user_id))
            else:
                # 如果不存在，则插入新的行
                insert_query = "INSERT INTO clickthroughrate (blog_id, user_id, click) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (blog_id, user_id, click_value))

            g.connection.commit()

            return jsonify({'success': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询点击率
@app.route('/get_clickthroughrate', methods=['POST'])
def get_clickthroughrate():
    data = request.get_json()

    if 'blog_id' not in data:
        return jsonify({'error': '缺少blog_id'}), 400

    blog_id = data['blog_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询对应blog_id的行，将click列的数值相加
            query = "SELECT SUM(click) AS total_click FROM clickthroughrate WHERE blog_id = %s"
            cursor.execute(query, (blog_id,))
            result = cursor.fetchone()

            if result:
                total_click = result['total_click'] or 0
                return jsonify({'success': 200, 'total_click': total_click}), 200
            else:
                return jsonify({'error': '找不到对应的点击率数据'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 检查收藏状态
@app.route('/check_collection_status', methods=['POST'])
def check_collection_status():
    data = request.get_json()

    if 'blog_id' not in data or 'user_id' not in data:
        return jsonify({'error': '缺少blog_id或user_id'}), 400

    blog_id = data['blog_id']
    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询收藏表，检查是否有匹配的记录
            select_query = "SELECT * FROM collect WHERE blog_id = %s AND user_id = %s"
            cursor.execute(select_query, (blog_id, user_id))
            result = cursor.fetchone()

            is_collected = result is not None

            return jsonify({'success': True, 'is_collected': is_collected}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 收藏文章
@app.route('/add_to_collection', methods=['POST'])
def add_to_collection():
    data = request.get_json()

    if 'blog_id' not in data or 'user_id' not in data:
        return jsonify({'error': '缺少blog_id或user_id'}), 400

    blog_id = data['blog_id']
    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 插入数据到收藏表
            insert_query = "INSERT INTO collect (blog_id, user_id) VALUES (%s, %s)"
            cursor.execute(insert_query, (blog_id, user_id))
            g.connection.commit()

            return jsonify({'success': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 取消收藏文章
@app.route('/remove_from_collection', methods=['POST'])
def remove_from_collection():
    data = request.get_json()

    if 'blog_id' not in data or 'user_id' not in data:
        return jsonify({'error': '缺少blog_id或user_id'}), 400

    blog_id = data['blog_id']
    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 删除收藏表中对应的记录
            delete_query = "DELETE FROM collect WHERE blog_id = %s AND user_id = %s"
            cursor.execute(delete_query, (blog_id, user_id))
            g.connection.commit()

            return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询用户收藏的文章
@app.route('/get_user_collection', methods=['POST'])
def get_user_collection():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': '缺少user_id'}), 400

    user_id = data['user_id']


    with g.connection.cursor() as cursor:
       # 查询用户收藏的文章
       query = """
           SELECT blog.id, blog.title
           FROM collect
           INNER JOIN blog ON collect.blog_id = blog.id
           WHERE collect.user_id = %s
       """
       cursor.execute(query, (user_id,))
       result = cursor.fetchall()

       if result:
           return jsonify({'success': 200, 'collection': result}), 200
       else:
           return jsonify({'error': '用户没有收藏的文章'}), 404



# 关注用户
@app.route('/follow_user', methods=['POST'])
def follow_user():
    data = request.get_json()

    if 'user_id_1' not in data or 'user_id_2' not in data:
        return jsonify({'error': '缺少user_id_1或user_id_2'}), 400

    user_id_1 = data['user_id_1']
    user_id_2 = data['user_id_2']

    try:
        with g.connection.cursor() as cursor:
            # 插入关注关系到关注表
            insert_query = "INSERT INTO concern (user_id_1, user_id_2) VALUES (%s, %s)"
            cursor.execute(insert_query, (user_id_1, user_id_2))
            g.connection.commit()

            return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询关注用户
@app.route('/get_following_users', methods=['POST'])
def get_following_users():
    data = request.get_json()

    if 'user_ids' not in data:
        return jsonify({'error': '缺少user_ids'}), 400

    user_ids = data['user_ids']


    with g.connection.cursor() as cursor:
        # 查询被关注用户的用户名
        query = """
            SELECT tb_user.id, tb_user.username
            FROM concern
            INNER JOIN tb_user ON concern.user_id_2 = tb_user.id
            WHERE concern.user_id_1 IN (%s)
        """
        in_clause = ', '.join(['%s'] * len(user_ids))
        cursor.execute(query % in_clause, tuple(user_ids))
        result = cursor.fetchall()
        if result:
            return jsonify({'success': True, 'following_users': result}), 200
        else:
            return jsonify({'success': '404'})



# 检查是否关注
@app.route('/check_following', methods=['POST'])
def check_following():
    data = request.get_json()

    if 'user_id_1' not in data or 'user_id_2' not in data:
        return jsonify({'error': 'Missing user_id_1 or user_id_2'}), 400

    user_id_1 = data['user_id_1']
    user_id_2 = data['user_id_2']
    print(user_id_1, user_id_2)
    with g.connection.cursor() as cursor:
        query = "SELECT * FROM concern WHERE user_id_1 = %s AND user_id_2 = %s"
        cursor.execute(query, (user_id_1, user_id_2))
        result = cursor.fetchone()
        if result:
            return jsonify({'is_following': True})
        else:
            return jsonify({'is_following': False})


# 查询粉丝用户
@app.route('/get_followers', methods=['POST'])
def get_followers():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': '缺少user_id'}), 400

    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询被关注用户的用户名
            query = """
                SELECT tb_user.id, tb_user.username
                FROM concern
                INNER JOIN tb_user ON concern.user_id_1 = tb_user.id
                WHERE concern.user_id_2 = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchall()

            if result:
                return jsonify({'success': True, 'followers': result}), 200
            else:
                return jsonify({'error': '找不到被关注的用户信息'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 取消关注
@app.route('/unfollow_user', methods=['POST'])
def unfollow_user():
    data = request.get_json()

    if 'user_id_1' not in data or 'user_id_2' not in data:
        return jsonify({'error': '缺少user_id_1或user_id_2'}), 400

    user_id_1 = data['user_id_1']
    user_id_2 = data['user_id_2']

    try:
        with g.connection.cursor() as cursor:
            # 删除关注关系
            delete_query = "DELETE FROM concern WHERE user_id_1 = %s AND user_id_2 = %s"
            cursor.execute(delete_query, (user_id_1, user_id_2))
            g.connection.commit()

            return jsonify({'success': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower()


# 上传附件
@app.route('/upload_file', methods=['POST'])
def upload_file():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': '400'}),

    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 将文件保存到指定路径
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # 返回文件保存的相对路径
        return jsonify({'success': True, 'file_path': os.path.join(app.config['UPLOAD_FOLDER'], filename)})

    return jsonify({'error': '文件类型不允许' ,'status': 400})

@app.route('/download_annex', methods=['GET'])
def download_annex():
    blog_id = request.args.get('blog_id')

    # 根据blog_id查询附件数据
    with g.connection.cursor() as cursor:
        select_annex_query = "SELECT route FROM annex WHERE blog_id = %s"
        cursor.execute(select_annex_query, (blog_id,))
        annex_data = cursor.fetchone()

    if annex_data:
        annex_path = annex_data['route']
        return send_file(annex_path, as_attachment=True, mimetype='application/octet-stream')
    else:
        return jsonify({'message': '未找到附件', 'status': 404})
# 删除附件
@app.route('/delete_annex', methods=['POST'])
def delete_annex():
    data = request.get_json()

    if 'annex_id' not in data:
        return jsonify({'error': '缺少annex_id'}), 400

    annex_id = data['annex_id']

    try:
        with g.connection.cursor() as cursor:
            # 删除附件表中对应的记录
            delete_query = "DELETE FROM annex WHERE id = %s"
            cursor.execute(delete_query, (annex_id,))
            g.connection.commit()

            return jsonify({'success': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 新增评论
@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.get_json()

    if 'text' not in data or 'create_time' not in data or 'blog_id' not in data or 'user_id' not in data:
        return jsonify({'error': '缺少text、create_time、blog_id或user_id'}), 400

    text = data['text']
    create_time = data['create_time']
    blog_id = data['blog_id']
    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 插入数据到评论表
            insert_query = "INSERT INTO comment (text, create_time, blog_id, user_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (text, create_time, blog_id, user_id))
            g.connection.commit()

            return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询评论
@app.route('/get_comments', methods=['POST'])
def get_comments():
    data = request.get_json()

    if 'blog_id' not in data or 'user_id' not in data:
        return jsonify({'error': '缺少blog_id或user_id'}), 400

    blog_id = data['blog_id']
    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询评论信息
            query = "SELECT id, text, create_time FROM comment WHERE blog_id = %s AND user_id = %s"
            cursor.execute(query, (blog_id, user_id))
            comments = cursor.fetchall()

            return jsonify({'success': 200, 'comments': comments}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询个人评论
@app.route('/get_comments_g', methods=['POST'])
def get_comments_g():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': '或user_id'}), 400

    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询评论信息
            query = "SELECT id, text, create_time FROM comment WHERE user_id = %s"
            cursor.execute(query, user_id)
            comments = cursor.fetchall()

            return jsonify({'success': 200, 'comments': comments}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 后台查询评论
@app.route('/get_comments_h', methods=['GET'])
def get_comments_h():
    try:
        with g.connection.cursor() as cursor:
            # Select the required fields from the comment table
            query = """
                SELECT comment.id AS comment_id, comment.text, comment.create_time, 
                       comment.blog_id, comment.user_id,
                       blog.title AS article_title, tb_user.username AS commenter_username
                FROM comment
                JOIN blog ON comment.blog_id = blog.id
                JOIN tb_user ON comment.user_id = tb_user.id
            """

            cursor.execute(query)
            comments = cursor.fetchall()

            return jsonify({'status': 200, 'comments': comments}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 删除评论
@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    data = request.get_json()

    if 'comment_id' not in data:
        return jsonify({'error': '缺少comment_id'}), 400

    comment_id = data['comment_id']

    try:
        with g.connection.cursor() as cursor:
            # 删除评论回复表中相关联的记录
            delete_reply_query = "DELETE FROM comment_reply WHERE comment_id = %s"
            cursor.execute(delete_reply_query, (comment_id,))

            # 删除评论表中的记录
            delete_comment_query = "DELETE FROM comment WHERE id = %s"
            cursor.execute(delete_comment_query, (comment_id,))

            g.connection.commit()

            return jsonify({'status': 200, 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 新增评论回复
@app.route('/add_comment_reply', methods=['POST'])
def add_comment_reply():
    data = request.get_json()

    if 'text' not in data or 'create_time' not in data or 'blog_id' not in data or 'user_id' not in data or 'comment_id' not in data:
        return jsonify({'error': '缺少text、create_time、blog_id、user_id或comment_id'}), 400

    text = data['text']
    create_time = data['create_time']
    blog_id = data['blog_id']
    user_id = data['user_id']
    comment_id = data['comment_id']

    try:
        with g.connection.cursor() as cursor:
            # 插入数据到回复评论表
            insert_query = "INSERT INTO comment_reply (text, create_time, blog_id, user_id, comment_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (text, create_time, blog_id, user_id, comment_id))
            g.connection.commit()

            return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询评论回复
@app.route('/get_comment_replies', methods=['POST'])
def get_comment_replies():
    data = request.get_json()

    if 'blog_id' not in data or 'comment_id' not in data:
        return jsonify({'error': '缺少blog_id或comment_id'}), 400

    blog_id = data['blog_id']
    comment_id = data['comment_id']

    try:
        with g.connection.cursor() as cursor:
            # 查询回复评论信息
            query = "SELECT id, text FROM comment_reply WHERE blog_id = %s AND comment_id = %s"
            cursor.execute(query, (blog_id, comment_id))
            comment_replies = cursor.fetchall()

            return jsonify({'success': True, 'comment_replies': comment_replies}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 修改评论
@app.route('/modify_comment', methods=['POST'])
def modify_comment():
    data = request.get_json()

    comment_id = data['comment_id']
    text = data['text']
    create_time = data['create_time']

    with g.connection.cursor() as cursor:
        # Update the comment with the provided data
        update_query = "UPDATE comment SET text=%s, create_time=%s WHERE id=%s"
        cursor.execute(update_query, (text, create_time, comment_id))
        g.connection.commit()

        return jsonify({'success': True}), 200



# 删除评论回复
@app.route('/delete_comment_reply', methods=['POST'])
def delete_comment_reply():
    data = request.get_json()

    if 'id' not in data:
        return jsonify({'error': '缺少id'}), 400

    comment_reply_id = data['id']

    try:
        with g.connection.cursor() as cursor:
            # 删除回复评论表中的记录
            delete_query = "DELETE FROM comment_reply WHERE id = %s"
            cursor.execute(delete_query, (comment_reply_id,))
            g.connection.commit()

            return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 查询用户评论
@app.route('/get_user_comments', methods=['POST'])
def get_user_comments():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': '缺少user_id'}), 400

    user_id = data['user_id']

    try:
        with g.connection.cursor() as cursor:
            # 执行查询
            query = """
                SELECT
                    c.id AS comment_id,
                    c.text AS comment_text,
                    c.create_time AS comment_time
                FROM
                    comment c
                JOIN
                    tb_user u ON c.user_id = u.id
                WHERE
                    u.id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchall()

            # 将查询结果转为 JSON 格式并返回
            comments = [{'comment_id': row['comment_id'], 'comment_text': row['comment_text'],
                         'comment_time': row['comment_time']} for row in result]
            return jsonify({'success': True, 'comments': comments}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 查询用户评论
@app.route('/get_user_comments2', methods=['POST'])
def get_user_comments2():
    # 从前端获取用户ID
    data = request.get_json()
    user_id = data.get('user_id')

    # 查询用户的所有评论
    with g.connection.cursor() as cursor:
        query = """
            SELECT
                comment.id AS comment_id,
                comment.text AS comment_text,
                comment.blog_id AS blog_id,
                blog.title AS blog_title,
                tb_user.username AS commenter,
                comment.create_time AS comment_time
            FROM
                comment
                JOIN blog ON comment.blog_id = blog.id
                JOIN tb_user ON comment.user_id = tb_user.id
            WHERE
                comment.user_id = %s
        """
        cursor.execute(query, (user_id,))
        user_comments = cursor.fetchall()
    # 构造返回的 JSON 数据
    result = []
    for comment in user_comments:
        result.append({
            'comment_id': comment['comment_id'],
            'comment_text': comment['comment_text'],
            'blog_id': comment['blog_id'],
            'blog_title': comment['blog_title'],
            'commenter': comment['commenter'],
            'comment_time': comment['comment_time'],
        })
    return jsonify({'user_comments': result})

# 后台查询评论
@app.route('/get_like_comments', methods=['POST'])
def get_like_comments():
    # 获取前端发送的搜索关键字
    data = request.get_json()
    search_keyword = data['search']
    print(search_keyword)

    with g.connection.cursor() as cursor:
        query = """
            SELECT
                b.title AS article_title,
                c.id AS comment_id,
                c.text,
                c.blog_id,
                c.user_id,
                u.username AS commenter_username,
                c.create_time
            FROM comment c
            LEFT JOIN blog b ON c.blog_id = b.id
            LEFT JOIN tb_user u ON c.user_id = u.id
            WHERE c.text LIKE %s;
        """

        # 执行查询
        cursor.execute(query, ('%' + search_keyword + '%',))
        comments = cursor.fetchall()

    # 构建符合期望的 JSON 结构
    formatted_comments = [
        {
            "article_title": comment["article_title"],
            "blog_id": comment["blog_id"],
            "comment_id": comment["comment_id"],
            "commenter_username": comment["commenter_username"],
            "create_time": str(comment["create_time"]),  # 将日期转换为字符串
            "text": comment["text"],
            "user_id": comment["user_id"]
        }
        for comment in comments
    ]

    return jsonify({'status': 200, 'comments': formatted_comments}), 200


# 查询用户部分数据
@app.route('/get_user_data', methods=['POST'])
def get_user_data():
    data = request.get_json()
    username = data['username']
    # 使用数据库连接创建游标
    with g.connection.cursor() as cursor:
        sql = """
            SELECT
                u.id AS user_id,
                u.username,
                IFNULL(COUNT(b.id), 0) AS article_count
            FROM
                tb_user u
            LEFT JOIN
                blog b ON u.id = b.user_id
            WHERE
                u.username = %s
            GROUP BY
                u.id
        """
        cursor.execute(sql, (username,))
        user_data = cursor.fetchone()
        if user_data:
            return jsonify(user_data)
        else:
            return jsonify({"error": "User not found"}), 404

# 路由：获取用户信息
@app.route('/get_user_info', methods=['POST'])
def get_user_info():
    try:
        # 获取前端传递的用户id
        data = request.get_json()
        user_id = data.get('user_id')

        # 查询用户信息
        with g.connection.cursor() as cursor:
            # 查询用户基本信息
            user_info_query = "SELECT id, username FROM tb_user WHERE id = %s"
            cursor.execute(user_info_query, (user_id,))
            user_info_result = cursor.fetchone()

            if not user_info_result:
                return jsonify({'error': 'User not found'}), 404

            user_name = user_info_result['username']

            # 查询关注数
            follow_count_query = "SELECT COUNT(*) as follow_count FROM concern WHERE user_id_1 = %s"
            cursor.execute(follow_count_query, (user_id,))
            follow_count_result = cursor.fetchone()
            follow_count = follow_count_result['follow_count']

            # 查询收藏文章数
            collect_count_query = "SELECT COUNT(*) as collect_count FROM collect WHERE user_id = %s"
            cursor.execute(collect_count_query, (user_id,))
            collect_count_result = cursor.fetchone()
            collect_count = collect_count_result['collect_count']

        # 构建返回的用户信息json
        user_info = {
            'user_id': user_id,
            'user_name': user_name,
            'follow_count': follow_count,
            'collect_count': collect_count
        }

        return jsonify(user_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 路由：获取用户收藏的文章
@app.route('/get_user_collected_articles', methods=['POST'])
def get_user_collected_articles():

    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'error': 'Missing user_id'}), 400
    user_id = data['user_id']
    with g.connection.cursor() as cursor:
        query = """
            SELECT blog.id, blog.title
            FROM collect
            INNER JOIN blog ON collect.blog_id = blog.id
            WHERE collect.user_id = %s
        """
        cursor.execute(query, (user_id,))
        collected_articles = cursor.fetchall()
        return jsonify({'success': True, 'collected_articles': collected_articles}), 200

# 获取用户收藏的文章
@app.route('/get_user_collected_articles2', methods=['POST'])
def get_user_collected_articles2():
    data = request.get_json()
    user_id = data.get('user_id')
    with g.connection.cursor() as cursor:
        query = """
            SELECT blog.id , blog.title1, blog.title2,
                   blog.title, tb_user.username, blog.creat_time
            FROM collect
            JOIN blog ON collect.blog_id = blog.id
            JOIN tb_user ON blog.user_id = tb_user.id
            WHERE collect.user_id = %s
            """
        cursor.execute(query, (user_id,))
        collected_articles = cursor.fetchall()
    # 返回查询结果
    return jsonify({'status': '200', 'collected_articles': collected_articles})


# 获取用户关注的用户
@app.route('/get_user_concerned_articles', methods=['POST'])
def get_user_concerned_articles():
    data = request.get_json()

    user_id = data['user_id']
    with g.connection.cursor() as cursor:
        query = """
            SELECT user_id_2, username
            FROM concern
            INNER JOIN tb_user ON concern.user_id_2 = tb_user.id
            WHERE concern.user_id_1 = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        if result:
            return jsonify({'success': True, 'following_users': result}), 200
        else:
            return jsonify({'success': True, 'following_users': 0}), 200


if __name__ == '__main__':
    app.run()
