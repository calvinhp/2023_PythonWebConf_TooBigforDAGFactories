import datetime

from flask import Flask

app = Flask(__name__)

tasks = {}

task_duration = datetime.timedelta(seconds=10)


@app.route("/submit/<name>")
# Creating a function named success
def submit(name):
    tasks[name] = datetime.datetime.now()

    print(f"Submitted {name} at {tasks[name]}")

    return f"{name} Submitted Successfully"


@app.route("/status/<name>")
def status(name):
    if name in tasks:
        if tasks[name] + task_duration > datetime.datetime.now():
            return "Running"
        else:
            return "Complete"
    else:
        return "Not Found"


# Programs executes from here in a development server (locally on your system)
# with debugging enabled.

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
