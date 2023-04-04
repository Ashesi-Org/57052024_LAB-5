# Import the necessary libraries
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
import functions_framework

# Create an instance of the Flask application
app = Flask(__name__)

# Set up the database configurations
db_credentials = credentials.Certificate('school-6c171-firebase-adminsdk-ac2wb-d133d067af.json')
firebase_app = initialize_app(db_credentials)
db = firestore.client()

# Define the database collections
voters_ref = db.collection("voters")
elections_ref = db.collection("elections")

# Define a route for the home page
@app.route("/")
def index():
    """
    This function returns a simple greeting message to the user.
    """
    return "Hello, welcome to my voting application!"

# Add additional functionality to the app, such as error handling or input validation

# Create a new voter by registering their information into the database
@app.route("/register", methods=["POST"])
def register_voter():
    """
    This function creates a new account by adding user information to the database.
    """
    # Check if there is any user data inserted
    if not request.json:
        return jsonify({"message": "Please provide user information"}), 400 

    id = request.json["id"]
    
    # Check if the account with the given ID already exists in the database
    account_info = voters_ref.document(id).get()
    if not account_info.exists:
        voters_ref.document(id).set(request.json)
    else:
        return jsonify({"error": "Account already exists"}), 403

    return jsonify({"message": "Account created successfully", "data": request.json}), 200



# Remove a voter from the database by their ID
@app.route("/deregister/<id>", methods=["DELETE"])
def deregister(id):
    """
    This function removes a voter from the database using their ID.
    """
    voter_details = voters_ref.document(id).get()
    if voter_details.exists:
        voters_ref.document(id).delete()
        return jsonify({"message": 'The voter with has been deleted'})
    return jsonify({"message": 'The voter does not exist'}), 404




@app.route("/update/<id>", methods=["PATCH"])
def update(id):

    voter_details = voters_ref.document(id).get()

    if voter_details.exists:
        voters_ref.document(id).update(request.data)
        return jsonify({ "data": request.data})
    return jsonify({"message": 'User  does not exist'})


@app.route("/retrieve/<id>", methods=["GET"])
def retrieve_voter(id):
        voter_details = voters_ref.document(id).get()
        if voter_details.exists:
            return jsonify({"data": voter_details.to_dict()})
        return jsonify({'error': 'User with ID  does not exist'}), 404



# ELECTIONS 

# CREATING A NEW ELECTION
@app.route("/create_election", methods=["POST"])
def create_election():

    election_id = request.json["election_id"]

    election_details = elections_ref.document(election_id)

    if election_details.get().exists:
        return jsonify({"error": "Election already exists"}), 403

    election_details.set(request.json)
    return jsonify({"message": "Election created successfully", "data": request.json})


# RETRIEVING AN ELECTION WITH ITS DETAILS USING THE ELECTIONS' ID
@app.route("/retrieve_election/<id>", methods=["GET"])
def retrieve_election(id):
    election_details = elections_ref.document(id)

    if not election_details.get().exists:
        return jsonify({"message": "The election with ID does not exist"}), 404

    return jsonify({"data": elections_ref.get().to_dict()})



# DELETING AN ELECTION
@app.route("/delete_election/<id>", methods=["DELETE"])
def delete_election(id):
    
    election_details = elections_ref.document(id)

    if election_details.get().exists:
        elections_ref.document(id).delete()
        return jsonify({"message": f'Election with has been deleted'}), 204
    return jsonify({"message": f'The election with does not exist'}), 404


# VOTING IN AN ELECTION
@app.route("/elections/<election_id>/voters/<voter_id>/candidates/<candidate_id>", methods=["PATCH"])
def cast_vote(election_id, voter_id, candidate_id):

        election_details = elections_ref.document(election_id).get()
        voter_info = voters_ref.document(voter_id).get()

        if not election_details.exists:
            return jsonify({"message": f'Election with does not exist'}), 404
        elif not voter_info.exists:
            return jsonify({"message": f'Voter oes not exist'}), 404
        
        else:   
            if election_details.exists and voter_info.exists:
                data = election_details.to_dict()

                if voter_id in data["voters"]:
                    return jsonify({"message": "You have already voted"}), 403
                else:
                    for candidate in data["candidates"]:
                        if candidate["id"] == candidate_id:
                            candidate["total_votes"] += 1
                            elections_ref.document(election_id).update({"candidates": data["candidates"]})
                            elections_ref.document(election_id).update({"voters": firestore.ArrayUnion([voter_id])})
                            return jsonify({"message": "Your vote has been recorded successfully"}), 200
                    return jsonify({"message": "Candidate not found"}), 404



@functions_framework.http
def voters_api(request):
    if request.method == 'POST' and request.path == '/register':
        return register_voter()
    elif request.method == 'POST' and request.path == '/create_election':
        return create_election()
    else:
        internal_ctx = app.test_request_context(path=request.full_path, method=request.method)
        internal_ctx.request.data = request.data
        internal_ctx.request.headers = request.headers

        internal_ctx.push()

        #Dispatch the request to the internal app and get the result 
        return_value = app.full_dispatch_request()
        #Offload the context
        internal_ctx.pop()
        
        #Return the result of the internal app routing and processing      
        return return_value

if __name__ == "__main__":
    app.run(debug = True)