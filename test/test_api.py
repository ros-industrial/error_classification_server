import json
import requests

# Simple Interactive Test to test the API routes

# Test case - ERROR
# errorText = "Aborting because the robot appears to be oscillating over and over. Even after executing all recovery behaviors"

# Test case - WARN Turtlebot
errorText = "Rotation cmd in collision"

# Test case - Info Turtlebot
# errorText = "Got new plan"

# Test case - NO RESULT
# errorText = "Sample dummy error text."

# Test case - tests pattern matching
# errorText = "Clearing both costmaps to unstuck robot (3.00m)."
# errorText = "Clearing both costmaps to unstuck robot (1.84m)."

# Test case - tests case insensitivity
# errorText = "got new plan"
# errorText = "GOT NEW PLAN"

robotModel = "Turtlebot3"
query_params = {'RobotModel': robotModel, 'ErrorText': errorText}
print('API Query Parameters: ', query_params)

print('API PING RESPONSE')
error_response = requests.get('http://localhost:8000' + '/ping')
print(error_response)
error_resp_content = json.loads(error_response.content)
error_data = error_resp_content['data']
print(error_data)

print('ERT RESPONSE')
error_response = requests.get('http://localhost:8000' + '/ert/error-data/', params = query_params)
print(error_response)
error_resp_content = json.loads(error_response.content)
error_data = error_resp_content['data']
print(error_data)

print('ECS RESPONSE')
error_response = requests.get('http://localhost:8000' + '/ecs/error-data/', params = query_params)
print(error_response)
error_resp_content = json.loads(error_response.content)
error_data = error_resp_content['data']
print(error_data)