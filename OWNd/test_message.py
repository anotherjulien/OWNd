from message import OWNMessage

message = OWNMessage.parse("*4*4001#5*0#1##")

print(message)

print(message.unique_id)
print(message.entity)

print(message.message_type)
print(message.set_temperature)