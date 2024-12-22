from flask import Flask, render_template, session, request, redirect, url_for, send_file, jsonify
import pymysql, os
from datetime import timedelta
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

# MYsql 연동
db = pymysql.connect(
    host='localhost',
    user='root',
    password='toor',
    database='flaskDB',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

#세션에 대한 키값을 설정
app.secret_key = 'sample_secret'
#세션 유지 시간 설정
app.permanent_session_lifetime = timedelta(minutes=30)

# 업로드된 파일을 저장할 폴더
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 허용할 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


 # 기본 index 페이지
@app.route('/')
def index():
 if 'name' in session:
     username = session['name']

     return render_template('index.html', logininfo = username)
 else:
     username = None
     return render_template('index.html', logininfo = username)


#로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['id']
        user_pw = request.form['pw']

        cursor = db.cursor()
        query = "SELECT * FROM member WHERE user_id = %s AND user_password = %s"
        value = (user_id, user_pw)
        cursor.execute(query, value)
        data = cursor.fetchall()
        cursor.close()

        # 사용자가 존재하는지 확인
        if data:
            # 로그인 성공 시 세션에 user_id와 name 저장
            session['ID'] = user_id
            session['name'] = data[0]['name'] 
            return render_template('index.html', logininfo=user_id)
        else:
            # 로그인 실패 시 오류 페이지로 이동
            return render_template('loginError.html')
    else:
        # GET 요청 시 로그인 페이지 표시
        return render_template('login.html')
    
   
#아이디/비밀번호 찾기 폼
@app.route('/find', methods=['GET', 'POST'])
def find():
    return render_template('find.html') 
   
   
   
@app.route('/idfind', methods=['GET', 'POST'])
def idfind():
    if request.method == 'POST':
        name = request.form['name']
        school = request.form['school']
        
        # DB에서 해당 아이디와 학교명으로 사용자 검색
        with db.cursor() as cursor:
            cursor.execute("SELECT user_id FROM member WHERE name = %s AND school = %s", (name, school))
            user = cursor.fetchone()  # 튜플 형태로 반환
        
        if user:
            # user_id를 템플릿에 전달 (튜플의 첫 번째 값이 user_id)
            return render_template('idfind.html', user_id=user['user_id'])
        else:
            return render_template('idfind.html', user_id="아이디를 찾을 수 없습니다.")
    return render_template('find.html')  # GET 요청에 대한 응답

# 비밀번호 찾기
@app.route('/pwfind', methods=['GET', 'POST'])
def pwfind():
    if request.method == 'POST':
        user_id = request.form['id']  # 아이디
        school = request.form['school']  # 학교명

        # DB에서 해당 아이디, 이름, 학교명으로 사용자 검색
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM member WHERE user_id = %s AND school = %s", 
                           (user_id, school))
            user = cursor.fetchone()

        if user:
            return render_template('pwfind.html', user_password=user['user_password'])
        else:
            return render_template('pwfind.html', user_password="비밀번호를 찾을 수 없습니다.")

    return render_template('pwfind.html')  # GET 요청시 pwfind.html을 반환


@app.route('/regist', methods=['GET', 'POST'])
def regist():
    if request.method == 'POST':
        user_id = request.form['id']
        user_pw = request.form['pw']
        name = request.form['name']
        school = request.form['school']

        # 프로필 이미지 처리
        profile_image = request.files.get('profile_image')  # 파일을 가져옵니다.
        
        if profile_image and allowed_file(profile_image.filename):
            # 파일 이름 안전하게 처리
            filename = secure_filename(profile_image.filename)
            profile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(profile_image_path)  # 파일 저장

            # 저장된 파일 경로를 데이터베이스에 저장할 수 있도록 준비
            profile_image_url = f"/{profile_image_path}"

        else:
            profile_image_url = None  # 이미지가 없으면 None으로 설정

        # 아이디 중복 확인
        cursor = db.cursor()
        query = "SELECT * FROM member WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        data = cursor.fetchone()

        if data:
            return render_template('registError.html')
        else:
            # 데이터베이스에 프로필 이미지 경로 추가
            query = """INSERT INTO member (user_id, user_password, name, school, profile_image) 
                       VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (user_id, user_pw, name, school, profile_image_url))
            db.commit()  # 변경사항 저장
            return render_template('registSuccess.html')

    return render_template('regist.html')   

@app.route('/myprofile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        # 로그인한 사용자 정보 가져오기
        user_id = session.get('ID')
        if not user_id:
            return redirect('/login')  # 로그인하지 않은 경우 리디렉션
        
        cursor = db.cursor()
        cursor.execute("SELECT * FROM member WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()  # 사용자 정보 딕셔너리 반환

        return render_template('myprofile.html', user=user)  # 사용자 정보 전달

    if request.method == 'POST':
        user_id = session.get('ID')
        user_pw = request.form['pw']
        name = request.form['name']
        school = request.form['school']

        # 프로필 이미지 업데이트
        profile_image = request.files.get('profile_image')
        profile_image_url = None
        
        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            profile_image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            profile_image.save(profile_image_url)

        # 데이터베이스 업데이트
        cursor = db.cursor()
        cursor.execute("""
            UPDATE member
            SET user_password = %s, name = %s, school = %s, profile_image = %s
            WHERE user_id = %s
        """, (user_pw, name, school, profile_image_url, user_id))
        db.commit()

        return redirect('/myprofile')

@app.route('/logout')
def logout():
    session.clear()  # 세션에 저장된 모든 데이터 삭제
    return redirect('/')  

#게시판 페이지
@app.route('/post')
@app.route('/post/page/<int:page>')
def post(page=1):
    posts_per_page = 10
    offset = (page - 1) * posts_per_page
    search_query = request.args.get('search', '')
    search_option = request.args.get('search_option', 'all')

    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM boardtest")
        total_posts = cursor.fetchone()['total']
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page

        # 검색 옵션에 따른 쿼리 변경
        if search_option == 'title':
            cursor.execute(
                "SELECT * FROM boardtest WHERE title LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s",
                ('%' + search_query + '%', posts_per_page, offset)
            )
        elif search_option == 'content':
            cursor.execute(
                "SELECT * FROM boardtest WHERE content LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s",
                ('%' + search_query + '%', posts_per_page, offset)
            )
        elif search_option == 'all':
            cursor.execute(
                "SELECT * FROM boardtest WHERE title LIKE %s OR content LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s",
                ('%' + search_query + '%', '%' + search_query + '%', posts_per_page, offset)
            )

        posts = cursor.fetchall()

    return render_template('post.html', postlist=posts, total_pages=total_pages, current_page=page, search=search_query, search_option=search_option)


@app.route('/post/content/<int:id>')
def content(id):
    with db.cursor() as cursor:
        # 조회수 증가
        cursor.execute("UPDATE boardtest SET view = view + 1 WHERE id = %s", (id,))
        db.commit()
        
        # 게시글 내용 가져오기
        cursor.execute("SELECT * FROM boardtest WHERE id = %s", (id,))
        post = cursor.fetchall()

    return render_template('content.html', data=post)


# 프로필 페이지 (다른 사용자도 프로필을 볼 수 있도록 수정)
@app.route('/profiletest/<string:name>', methods=['GET'])
def user_profile(name):
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM member WHERE name = %s", (name,))
        user = cursor.fetchone()

    # 사용자 정보가 존재하면 프로필 페이지로 반환
    if user:
        # 로그인한 사용자 정보를 확인
        logged_in_user_id = session.get('ID')

        # 프로필 페이지에 전달할 변수 추가
        return render_template('profiletest.html', user=user, logged_in_user_id=logged_in_user_id)
    else:
        return "사용자 정보를 찾을 수 없습니다.", 404



@app.route('/post/download/<int:id>')
def download_file(id):
    with db.cursor() as cursor:
        # 데이터베이스에서 파일 데이터와 제목 가져오기
        cursor.execute("SELECT file_data, title FROM boardtest WHERE id = %s", (id,))
        post = cursor.fetchone()

    if post and post['file_data']:
        file_data = post['file_data']  # 파일 데이터
        file_name = post['title']  # 제목 (파일명으로 사용)

        # 파일 형식 지정 (예: jpg로 가정)
        return send_file(BytesIO(file_data), as_attachment=True, download_name=f"{file_name}.jpg")
    else:
        return "파일을 찾을 수 없습니다.", 404


@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        title = request.form['title']
        name = session.get('name') 
        content = request.form['content']
        secret = 1 if 'secret' in request.form else 0 
        
        file = request.files.get('file')
        file_data = None

        if file:
            file_data = file.read()  # 파일을 읽어서 바이너리 데이터로 변환

        
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO boardtest (name, title, content, secret, file_data) VALUES (%s, %s, %s, %s, %s)",
                (name, title, content, secret, file_data)
            )
            db.commit()
        return redirect('/post')
    return render_template('write.html')


@app.route('/post/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        secret = request.form.get('secret')
        secret = True if secret == '1' else False
        
        # 파일 업로드 처리
        file = request.files.get('file_data')
        file_path = None
        if file:
            # 파일이 존재하면 저장
            filename = file.filename
            file_path = os.path.join('uploads', filename)
            file.save(file_path)
        
        # DB 업데이트
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE boardtest SET title = %s, content = %s, secret = %s, file_data = %s WHERE id = %s",
                (title, content, secret, file_path, id)
            )
            db.commit()
        
        return redirect(f'/post/content/{id}')
    
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM boardtest WHERE id = %s", (id,))
        post = cursor.fetchall()
    return render_template('edit.html', data=post)




@app.route('/post/delete/<int:id>')
def delete(id):
    return render_template('delete.html', id=id)


@app.route('/post/delete/success/<int:id>')
def delete_success(id):
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM boardtest WHERE id = %s", (id,))
        db.commit()
        # Reset the ID values after deletion
        cursor.execute("SET @new_id = 0;")
        cursor.execute("UPDATE boardtest SET id = (@new_id := @new_id + 1);")
        cursor.execute("ALTER TABLE boardtest AUTO_INCREMENT = 1;")
        db.commit()
    return redirect('/post')


if __name__ == '__main__':
    app.run(debug=True)
