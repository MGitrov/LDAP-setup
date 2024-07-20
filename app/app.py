from flask import Flask, request, render_template, redirect, url_for, flash, session
from ldap3 import Server, Connection, SIMPLE
import pyotp # Library used for generating and verifying TOTP tokens for MFA.
import qrcode # Library used for generating QR codes.

# io and base64 are used for handling image data for the QR code.
import io
import base64

app = Flask(__name__)  # Initiates a Flask application instance.
app.secret_key = "dummy_secret_key" # A random string used by Flask to secure things like sessions, cookies, etc.

LDAP_SERVER = "ldap://ldap-server"  # The URL of the LDAP server.
# As the LDAP server is running on a container, I need to specify the name of the container as part of the URL.

BASE_DN = "dc=my-domain,dc=com"  # The base distinguished name (DN) for the LDAP directory. Represents the root of the LDAP tree.
# In other words, specifies the starting point in the LDAP directory tree for searches.

# What DN is used to login to the LDAP directory to perform searches and other operations.
BIND_DN = "cn=admin,dc=my-domain,dc=com"
BIND_PASSWORD = "admin_password"

user_secrets = {} # Stores each user's unique generated secret, keyed by the username.

@app.route("/")
def index():
    if "authenticated" in session:
        return redirect(url_for("welcome"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_dn = f"uid={username},ou=Users,{BASE_DN}"  # Constructs user's DN based on the provided username and the "BASE_DN".

        try:
            server = Server(LDAP_SERVER)
            connection = Connection(server, user=user_dn, password=password, authentication=SIMPLE)  # Connects to the LDAP server using
            # a plaintext username and password for authentication.

            if connection.bind():
                session["username"] = username  # Stores the username in the current session.

                if username not in user_secrets:
                    secret = pyotp.random_base32()  # Generates a new secret (a random string of characters encoded in base32) for the current user.
                    user_secrets[username] = secret # Assigns the generated secret to the current user.
                    session["setup_mfa"] = True
                    return redirect(url_for("setup_mfa"))  # Redirects the user the to MFA setup.

                return redirect(url_for("mfa"))  # Redirects to MFA verification if the user already has a secret generated for him.

            else:
                flash("Invalid credentials", "danger")
                return redirect(url_for("login"))

        except Exception as error:
            flash(f"Error: {str(error)}", "danger")
            return redirect(url_for("login"))

    return render_template("login.html") # Handles the GET request by rendering the login form.

@app.route("/setup_mfa")
def setup_mfa():
    if "username" not in session or "setup_mfa" not in session: # Checks if the user is logged in.
        return redirect(url_for("login"))

    username = session["username"]
    secret = user_secrets[username]
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="ldap-setup") # Creates the TOTP URI out of the user's
    # unique generated secret for the authenticator app to generate the TOTP token.

    img = qrcode.make(otp_uri) # Creates the QR code out of the TOTP URI created above.
    
    # Creates a buffer in memory to store the QR code image (instead of a file on disk).
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    img_str = base64.b64encode(buf.getvalue()).decode("ascii") # Converts the QR code image to a Base64 string to embed it in the HTML.

    return render_template("setup_mfa.html", qr_code=img_str)

@app.route("/mfa", methods=["GET", "POST"])
def mfa():
    if "username" not in session: # Checks if the user is logged in.
        return redirect(url_for("login"))

    if request.method == "POST":
        token = request.form["token"] # User's input token will be processed.
        username = session["username"]

        secret = user_secrets[username]
        totp = pyotp.TOTP(secret) # Generates the TOTP token for comparison with user's input token.
        if totp.verify(token):
            session.pop("setup_mfa", None) # Removes the "setup_mfa" flag.
            session["authenticated"] = True  # Sets the "authenticated" flag to true.
            flash("Login successful", "success")
            return redirect(url_for("welcome"))

        else:
            flash("Invalid MFA token", "danger")

    return render_template("mfa.html")

@app.route("/welcome")
def welcome():
    if "authenticated" not in session:
        return redirect(url_for("login"))

    return render_template("welcome.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    session.pop("authenticated", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Allows the Flask server to be accessed from any IP address.