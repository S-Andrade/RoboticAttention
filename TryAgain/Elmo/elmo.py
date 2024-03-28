import robot_client
from gtts import gTTS


robot_client.set_robot_model("elmo")
success, message, client = robot_client.connect("http://192.168.0.102:8001")

print(client.address)
print(client.ip)
#print(client.pan_min)


client.send_command("set_pan_torque", control=True)
client.send_command("set_pan", angle=-40)

client.send_command("set_tilt_torque", control=True)
client.send_command("set_tilt", angle=-8)

speech = gTTS("Olá migos", lang='pt')

speech_file = 'speech.mp3'
speech.save(speech_file)
 
client.Speak()