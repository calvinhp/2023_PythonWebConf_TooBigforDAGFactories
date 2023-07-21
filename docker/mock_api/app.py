import datetime

from flask import Flask

app = Flask(__name__)

tasks = {}

task_duration = datetime.timedelta(seconds=30)


@app.route("/submit/<name>")
# Creating a function named success
def submit(name):
    tasks[name] = datetime.datetime.now()

    app.logger.info(f"Submitted {name} at {tasks[name]}")

    return f"{name} Submitted Successfully"


@app.route("/status/<name>")
def status(name):
    if name in tasks:
        if tasks[name] + task_duration > datetime.datetime.now():
            res = "Running"
        else:
            res = "Complete"
    else:
        res = "Not Found"

    app.logger.info(f"Status of {name} is {res}")
    return res

# Programs executes from here in a development server (locally on your system)
# with debugging enabled.

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
