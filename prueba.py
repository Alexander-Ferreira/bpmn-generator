import google.generativeai as genai
genai.configure(api_key='AIzaSyBcyunEhCQzYPyuemU0OIgPh0e3wjqI0SU')
model = genai.GenerativeModel('gemini-1.5-pro-latest')
response = model.generate_content("Genera XML BPMN para: cliente ordena producto")
print(response.text)
