from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Kullanıcı Kayıt Formu
class RegisterForm(Form): # Flask ile web programlama yapılırken formları HTML sayfalarında değil, python dosyası içinde oluşturuyoruz. Burada "Form" sınıfını inherit eden "RegisterForm" isimli bir form sınıfı oluşturduk. İlerde register() fonksiyonunda bu sınıftan bir form objesi oluşturup, bu objeyi register.html sayfasına parametre olarak göndereceğiz.
    name = StringField("İsim Soyisim:", validators=[validators.length(min=5, max=25)]) 
    username = StringField("Kullanıcı Adı:", validators=[validators.length(min=5, max=25)])
    email = StringField("Email Adresi:", validators=[validators.Email(message = "Lütfen geçerli bir email adresi giriniz.")])
    password = PasswordField("Parola:", validators=[validators.DataRequired(message="Lütfen bir parola belirleyiniz."), validators.EqualTo(fieldname = "confirm", message = "Parolalolar uyuşmuyor!")])
    confirm = PasswordField("Parola Doğrula:") # Formda şifrelerin yıldız şeklinde görünmesi için StringField yerine PasswordField kullandık.
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Kullanıcı Giriş Formu
class LoginForm(Form): # Aynı şekilde yukarıda kullanıcı kaydı için oluşturduğumuz RegisterForm sınıfı gibi, kullanıcı girişinde kullanmak üzere "LoginForm" isimli bir sınıf oluşturduk. Daha sonra login() fonksiyonunda bu sınıftan bir form objesi oluşturup, bu objeyi login.html sayfasına parametre olarak göndereceğiz.
    username = StringField("Kullanıcı Adı:")
    password = PasswordField("Parola:")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Makele Ekleme Formu
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators = [validators.length(min = 5, max = 100)])
    content = TextAreaField("Makale İçeriği", validators = [validators.length(min = 10)])
   
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "ybblog"

#MySQL veritabanı sunucusuna erişmek için için gereken yapılandırma
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Anasayfa
@app.route("/") # Hangi URL'nin hangi fonksiyonu tetikleyeceğini söylemek için app.route() fonksiyonunu kullanıyoruz. Bir url'yi bir fonksiyona bağlamak için bu dekoratörü kullanın. Bir URL girildiğinde hangi fonksiyonun çalışacağını söylemek için bu dekoratörü kullandık.
def index():
    articles = [
        {"id":1, "title":"Deneme1", "content":"Deneme 1 içeriği"},
        {"id":2, "title":"Deneme2", "content":"Deneme 2 içeriği"},
        {"id":3, "title":"Deneme3", "content":"Deneme 3 içeriği"}

    ]
    return render_template("index.html", answer = "yes", articles = articles)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query =  "select * from articles"
    result = cursor.execute(query)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    
    else:
        return render_template("articles.html")

    return render_template("articles.html")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Kullanıcı Kayıt İşlemi
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route("/register", methods = ["GET", "POST"])
def register():
    form  = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        query = "INSERT INTO USERS(name, email, username, password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash(message = "Kayıt işlemi başarıyla tamamlandı!", category = "success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html", form = form) # render_template fonksiyonu ilk parametredeki HTML sayfasını, içine form parametresini göndererek render'lıyor ve register() fonksiyonu bu HTML sayfasını cevap olarak döndürüyor.
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Login İşlemi
@app.route("/login", methods = ["GET", "POST"]) # Bu URL'ye bağlı fonksiyonun hem GET hem POST işlemi yapacağını belirtmek için "methods = ["GET","POST"]" parametresini veriyoruz. Default metod GET'tir.
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username_entered = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        query = "select * from users where username = %s"

        username_returned_value = cursor.execute(query, (username_entered,))

        if username_returned_value > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarıyla Giriş Yaptınız...", "success")
                session["logged_in"] = True
                session["username"] = username_entered
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış girdiniz!", "danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullanıcı bulunmamaktadır!", "danger")
            return redirect(url_for("login"))


    else:

        return render_template("login.html", form = form )
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Logout İşlemi
@app.route("/logout")
def logout():
    
    session.clear()
    flash("Başarıyla Çıkış Yaptınız...", "success")
    return redirect(url_for("index"))
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# Kullanıcı Giriş Decorator'ı (Giriş yapılmadan ulaşılamayacak sayfalara url üzerinden girişi engellemek için bu decorator'ı kullandık.)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.", "danger")
            return redirect(url_for("login"))
    return decorated_function


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "select * from articles where author = %s"
    result = cursor.execute(query,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Makale Ekleme
@app.route("/addArticle", methods = ["GET", "POST"])
@login_required
def addArticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        query = "insert into articles(title,author,content) values(%s,%s,%s) "
        cursor.execute(query, (title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Makale başarıyla eklendi.", "success")
        return redirect(url_for("dashboard"))

    else:

        return  render_template("addArticle.html", form = form)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    query = "select * from articles where id = %s"
    result = cursor.execute(query,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query1 = "select * from articles where author = %s and id = %s"
    result = cursor.execute(query1,(session["username"], id))

    if result > 0:
        query2 = "delete from articles where id = %s"
        cursor.execute(query2, (id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok veya bu makaleyi silme yetkiniz yok!", "danger")
        return redirect(url_for("index"))
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Makale Güncelleme
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "select * from articles where id = %s and author = %s"
        result = cursor.execute(query, (id, session["username"]))

        if result == 0:
            flash("Böyle bir makale bulunmuyor veya bu işleme yetkiniz yok!", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            
            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("edit.html", form = form)
    else:
        # POST Request
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        query1 = "update articles set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(query1, (newTitle, newContent, id))
        mysql.connection.commit()
        mysql.connection.close()
        
        flash("Makale başarıyla güncellendi!", "success")

        return redirect(url_for("dashboard"))
        
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Arama
@app.route("/search", methods = ["GET","POST"])
def search():

    if request.method == "GET":
        return  redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        query = "select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(query)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı!", "warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html", articles = articles)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


