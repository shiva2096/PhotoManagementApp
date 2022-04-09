
import json
import boto3
import requests


AMAZON_LEX_BOT = "Photo_Bot"
LEX_BOT_ALIAS = "photo_bot"
USER_ID = "user"


TABLENAME = 'photos'
ELASTIC_SEARCH_URL = "https://search-photos-47zfeio76xlqekg5ziusohr66m.us-east-1.es.amazonaws.com/_search?q="

S3_URL = "https://b2photostore.s3.amazonaws.com/"

def post_on_lex(query, user_id=USER_ID):
    """
    Get the user input from the frontend as text and pass
    it to lex. Lex will generate a new response.
    it will return a json response:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lex-runtime.html
    """
    client = boto3.client('lex-runtime')
    lex_response = client.post_text(botName=AMAZON_LEX_BOT,
                                    botAlias=LEX_BOT_ALIAS,
                                    userId=user_id,
                                    inputText=query)

    if lex_response['slots']['Label_one'] and lex_response['slots']['Label_two']:
        labels = 'labels:' + lex_response['slots']['Label_one'] + '+' + 'labels:' + lex_response['slots']['Label_two']
    elif lex_response['slots']['Label_one']:
        labels = 'labels:' + lex_response['slots']['Label_one']
    else:
        return
    return labels


def get_photos_ids(URL, labels):
    """
    return photos ids having the
    labels as desired
    """

    URL = URL + str(labels)
    #response = requests.get(URL, auth=awsauth).content
    response = requests.get(URL, auth=("admin","#Admin234")).content
    print("Response: ",response)
    data = json.loads(response)
    hits = data["hits"]["hits"]
    id_list = []
    labels_list = []
    for result in hits:
        _id = result["_source"]["objectKey"]
        id_list.append(_id)
        _labels = result["_source"]["labels"]
        labels_list.append(_labels)
    return id_list, labels_list


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin":"*",
            "Access-Control-Allow-Credentials" : True,
        },
    }

def lambda_handler(event, context):

    query = event['queryStringParameters']['q']
    #query = "Show me dog"
    labels = post_on_lex(query)
    id_list, labels_list = get_photos_ids(ELASTIC_SEARCH_URL, labels)

    results = []
    for i, l in zip(id_list, labels_list):
        results.append({"url": S3_URL + i, "labels": l})

    print(results)
    response = {"results": results}
    return respond(None, response)
