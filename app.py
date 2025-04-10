# Youtube video source link : https://www.youtube.com/watch?v=mkXdvs8H7TA&t=16s
# pip install flask
# pip install flask-socketio

from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio  import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"]="secret"
socketio = SocketIO(app)

rooms = {}

def generate_uniqe_code(Length): #Generating a unique codes
    while True:
        code = ""
        for _ in range(Length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break

    return code


@app.route("/", methods = ["POST", "GET"])
def home():
    session.clear() 
    if request.method=="POST": # Get data from the FORM
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        #Handling the create and join room functinalities
        if not name:
            return render_template("home.html", error = "Please enter a Name", code=code, name=name)
        if join != False and not code:
            return render_template("home.html", error="Please enter the room code", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_uniqe_code(5)
            rooms[room] = {"members":0, "messages":[]}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exists.", code=code, name=name)

        session["room"] = room # session used for storing the users data temp
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages = rooms[room]["messages"])
 
# Socket message handling
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message":data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

# Socket connection
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name":name, "message":"has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}") 

@socketio.on("disconnect")
def disconnect(auth):
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message":"left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug = True)