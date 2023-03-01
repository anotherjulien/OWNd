"""Manual testing of a message string"""

from OWNd.message_parser import parse_event

# message = OWNMessage.parse("*4*4001#5*0#1##")
message = parse_event("*9*0*3##")

print(message)
print(type(message))

print(message.unique_id)
print(message.entity)
print(message.channel)
print(message.is_on)
# print(message.message_type)
# print(message.set_temperature)
