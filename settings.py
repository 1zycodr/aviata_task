api_endpoint = 'https://api.skypicker.com/flights'
booking_api_endpoint = 'https://booking-api.skypicker.com/api/v0.1/check_flights'

headers = {'Content-Type': 'application/json'}

directions = (
    'ALA-TSE', 'TSE-ALA', 'ALA-MOW', 'MOW-ALA', 'ALA-CIT',
    'CIT-ALA', 'TSE-MOW', 'MOW-TSE', 'TSE-LED', 'LED-TSE'
)

locations = (
    'ALA', 'TSE', 'MOW', 'CIT', 'LED'
)

# max_attempts_to_recheck * recheck_delay should be equal to 5 minutes
max_attempts_to_recheck = 15
recheck_delay = 5
