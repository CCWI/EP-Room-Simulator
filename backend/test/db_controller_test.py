# TODO: write unit tests
from backend import db_controller, endpoint_request
from backend import utils

# create new sim
sim_id = endpoint_request.init_simulation()
encoded_data = utils.encode_byte_data_to_base64('test_idf_string'.encode())
endpoint_request.edit_idf_file(sim_id, encoded_data)
print(endpoint_request.get_simulation(sim_id))
print(db_controller.get_idf_data(sim_id))
