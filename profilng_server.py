from flask import Flask, render_template,request

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html', name='joe')
@app.route('/receiver', methods=['POST'])
def worker():
    return request.get_data()


if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
