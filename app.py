from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    submitted = request.method == "POST"
    return render_template("index.html", submitted=submitted)


if __name__ == "__main__":
    app.run(debug=True)
