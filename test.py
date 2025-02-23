from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def page():
    if request.method == "POST":
        round_id = request.form["round_id"]
        round_name = request.form["round_name"]
        start = request.form["start_date"]
        end = request.form["end_date"]
        matches = []

        for name, home, away, date in zip(request.form.getlist("match_name"), request.form.getlist("home"), request.form.getlist("away"), request.form.getlist("match_date")):
            matches.append({"id":f"{home}v{away}","name":name, "home":home, "away":away, "date":date})
        
        print("Round ID:", round_id)
        print("Round Name:", round_name)
        print("Start Date:", start)
        print("End Date:", end)
        print("Matches:")
        for match in matches:
            print("\t", match["id"])
            print("\t", match["name"])
            print("\t", match["home"])
            print("\t", match["away"])
            print("\t", match["date"])
            print("\n")

        return "You sent a POST request"
    teams = [{"id":"team1", "name":"Team 1"}, {"id":"team2", "name":"Team 2"}, {"id":"team3", "name":"Team 3"}, {"id":"team4", "name":"Team 4"}, {"id":"team5", "name":"Team 5"}, {"id":"team6", "name":"Team 6"}, {"id":"team7", "name":"Team 7"}, {"id":"team8", "name":"Team 8"}, {"id":"team9", "name":"Team 9"}, {"id":"team10", "name":"Team 10"}]
    return render_template("create_round.html", teams = teams)

app.run(port=5000)