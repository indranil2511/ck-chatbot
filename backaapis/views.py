from langchain.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from django.http import StreamingHttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain_community.document_loaders import TextLoader
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
import psycopg2
import traceback
load_dotenv()
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
client = OpenAI()

def get_moderation(question):
    """
    Check the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """
    response = client.moderations.create(input=question)
    categoryMap = dict(response.results[0].categories)
    if response.results[0].flagged:
        # get the categories that are flagged and generate a message
        return True
    return False
def event_stream(prompt,serialized_results):
  #INSTRUCTIONS = """
  #As a specialized QnA assistant named Zoe you have been trained to provide detailed information about CloudKaptan services and it\'s offerings, You are here to help users with any questions they may have about CloudKaptan. Encourage users to ask about CloudKaptan's product and offerings.
  #However, please note that You are specifically trained to respond to queries related to CloudKaptan only. Therefore, You should not provide information about other companies or unrelated topics outside of context.
  #If user queries about any other company or unrelated context, Please remind users to keep their questions focused on only CloudKaptan and not any other company or services, and You'll do Your best to provide accurate and helpful answers!
  #Your responses should be detailed and tailored only to the CONTEXT PROVIDED or any previous exchanges with the user. You may provide details about services from other vendors which CloudKaptan provide but end the response by letting the user know that Cloudkaptan has offerings regarding the service.
  #You will also ensure that the answer is relevant, accurate, detailed and coherent, and refrain from introducing any speculative or imaginative content. Prioritize factual accuracy and coherence in your response.
  #DO NOT under any circumstance build up your own response which is not present in the Context. For eg:- CONTEXT - DevOps, Question - What are the tools you use in Devops? The Answer should not mention about any tools but say that we have DevOps tool which we use for our clients. Always use the CONTEXT provided to generate helpful and professional response.\n
  #"""

  PROMPT = """ 
    Context:
    CloudKaptan is a company based out of India but has offices now opened in US and Australia. It is an IT solutions company. 
    You are an AI chatbot named Zoe to assist users with inquiries related to the products, services, and offerings of CloudKaptan. You need to generate responses based on the provided context and past conversations.
    You are espcially created solemnly to answer queries related to CloudKaptan ONLY.
    You can't answer anything not related to CloudKaptan company. 

    Instructions:
    1. Your responses should be solely based on the context provided. Do not generate speculative or imaginative content.
    2. Focus exclusively on CloudKaptan and refrain from providing information about other companies or unrelated topics.
    3. Utilize the provided context and reference previous conversations to generate relevant and accurate responses.
    4. Prioritize coherence and accuracy in your responses, ensuring they align with the user's queries and the context provided.
    5. Avoid hallucinations and refrain from making up answers not supported by the provided context.

    Example Queries with answers:
    - What cloud services does CloudKaptan offer?
    Answer -   CloudKaptan provide consultation and implemetation of following 
        * Salesforce
        * Q2 Lending
        * Data and Analytics
        * Quality Engineering
        * Digitl Services
        * AWS Cloud Apps
      It also provide Managed Servies through it's Annual Maintanance Services
      It also has product called Doclooper which is a reliable software tool that streamlines file transfers between SFTP locations and Salesforce organizations.
    - Can you provide information about Google pricing plans?
    Answer -  Sorry i am trained only on CloudKaptan related queries. I can't answer about any other companies. 
    - Tell me about AWS ?
    Answer - I can't give you direct information about AWS. You can ask me about CloudKaptan's implementation on AWS
    - Can you tell me about Google or Google Services ? 
    Answer - I am trained to answer queries related to CloudKaptan only. Anything other than it, i am unable to answer
    """
  TEMPERATURE = 0
  MAX_TOKENS = 700
  # limits how many questions we include in the prompt
  MAX_CONTEXT_QUESTIONS = 10
  conversationDb = psycopg2.connect(database=os.environ.get("PGVECTOR_DATABASE", "postgres"),
                                    user=os.environ.get("PGVECTOR_USER", "postgres"), 
                                    password=os.environ.get("PGVECTOR_PASSWORD", "priya"), 
                                    host=os.environ.get("PGVECTOR_HOST", "localhost"), 
                                    port=os.environ.get("PGVECTOR_PORT", "5434"))
  cursor = conversationDb.cursor()
  cursor.execute("SELECT * FROM chat_history")
  INSTRUCTIONS = PROMPT + f'CONTEXT : {serialized_results}'
  messages = [{"role": "system", "content": INSTRUCTIONS}]
  # Fetch all rows from the result set
  rows = cursor.fetchall()
  MAX_CONTEXT_QUESTIONS = len(rows)  if MAX_CONTEXT_QUESTIONS > len(rows) else MAX_CONTEXT_QUESTIONS
  # Print the retrieved data
  for row in rows[-MAX_CONTEXT_QUESTIONS:]:
    messages.append({ "role": "user", "content": row[1] })
    messages.append({ "role": "assistant", "content": row[2] })
    #print(f'Question:{row[1]}\nAnswer:{row[2]}')
  answer = ''
  messages.append({ "role": "user", "content": f'Question:{prompt}'})
  response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=messages,
      temperature=0,
      stream=True,
      max_tokens=MAX_TOKENS
  )
  chatcompletion_delta=""
  for chunk in response:
    chatcompletion_delta = chunk.choices[0].delta.content 
    if chatcompletion_delta:
      answer = answer + chatcompletion_delta
      yield chatcompletion_delta
  cursor.execute("INSERT INTO chat_history(question,answer) VALUES (%s, %s)", (prompt, answer))
  conversationDb.commit()
  conversationDb.close()

@csrf_exempt
def callToSearch(request):
    try:
      serialized_results = []
      embeddings = OpenAIEmbeddings()
      request_body_bytes = request.body
      request_body_str = request_body_bytes.decode('utf-8')
      request_data = json.loads(request_body_str)
      query = request_data['query']
      errors = get_moderation(query)
      if errors:
        errorList='Apologies, but I\'m unable to provide an answer to this question. If you have any specific inquiries about CloudKaptan, please don\'t hesitate to ask'
        return StreamingHttpResponse(errorList, content_type="text")
      CONNECTION_STRING = PGVector.connection_string_from_db_params(
      driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
      host=os.environ.get("PGVECTOR_HOST", "localhost"),
      port=int(os.environ.get("PGVECTOR_PORT", "5434")),
      database=os.environ.get("PGVECTOR_DATABASE", "postgres"),
      user=os.environ.get("PGVECTOR_USER", "postgres"),
      password=os.environ.get("PGVECTOR_PASSWORD", "priya"),
      )
      collection_name = 'CK_Articles'  
      db = PGVector(embedding_function=embeddings,
                                  collection_name= COLLECTION_NAME or collection_name,
                                  connection_string= CONNECTION_STRING )
      similar = db.similarity_search_with_score(query)
      for doc in similar:
        serialized_results.append(doc[0].page_content)
      response = StreamingHttpResponse(event_stream(query,serialized_results), content_type="text/event-stream")
      response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
      response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the data
    except Exception as e:
      print(e)
      traceback.print_exc()
      response = StreamingHttpResponse('Apologies an Internal Server Error has occured!', content_type="text")
      response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
      response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the data
    return response
@csrf_exempt
def vector():
    loader = TextLoader('./Cloudkaptan.txt', encoding='utf-8')
    documents = loader.load()
    vector.get_embedding(documents,"text-embedding-3-small")
    return JsonResponse('Success')