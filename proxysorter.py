"""
Gets messages from rabbitmq from proxy queue,
tries curl on different services
and then puts back to queue with service name, e.g. gravity
"""

import datetime
import os
import time

import pika
import requests
import yaml

#if no cloud config
#services=['gravity','revolutexpert']
#endpoints={}
#endpoints['gravity']='https://gravity-trade.com/ru/contacts'
#endpoints['revolutexpert']='https://revolutexpert.co/ru/contacts'


def fetch_config(url):
    """
    This function will download cloud yaml config
    """
    r = requests.get(url, allow_redirects=True)
    return r.content.decode("utf-8")


def publish_service_proxy(pip,q):
    """
    publish a message to MQ server
    """
    print ("publish to "+q+" start")
    try:
        credentialsP = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parametersP = pika.ConnectionParameters(RABBITMQ_SERVER,
                                       5672,
                                       '/',
                                       credentialsP)
        connectionP = pika.BlockingConnection(parametersP)
        channelP = connectionP.channel()

        channelP.queue_declare(queue=q)

        channelP.basic_publish(exchange='', routing_key=q, body=pip)
        print(" [x] "+pip)
        connectionP.close()
    except Exception as e:
        print(e)
        print("MQ failed, saved locally")




def service_check(pip):
    for service in services:
#       print ("checking seri "+service)
        endpoint=endpoints[service]
#       print ("checking end "+endpoint)
        start = datetime.datetime.now()
        req='curl '+endpoint+' -m 15 -x '+pip
        print(req)
#        time.sleep(1000)
        result = os.popen(req).read()
        end = datetime.datetime.now()
        diff = end - start
        diff=int(round(diff.microseconds / 1000))
        print (diff)

        print(result)
        verdict="bad"

        if 'html' in result.lower():
            verdict="good"

        if 'CAPTCHA' in result:
            verdict="bad"
            print('-------CAP________')

        print (verdict)
        if verdict=="good":
            publish_service_proxy(pip,service)
        time.sleep(5)
#        return verdict


if True:
    config=fetch_config('https://raw.githubusercontent.com/StopFraud/metadata/main/endpoints.yml')
    print (config)
    y=yaml.safe_load(config)
    l=(len(y))
    services=[]
    endpoints={}
    for i in range(0,l):
        services.append(y[i]["service"]["name"])
        endpoints[y[i]["service"]["name"]]=y[i]["service"]["endpoint"]
    print(services)
    print(endpoints)

    RABBITMQ_SERVER=os.getenv("RABBITMQ_SERVER")
    RABBITMQ_USER=os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD=os.getenv("RABBITMQ_PASSWORD")


    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)
        service_check(body.decode("utf-8"))


    if RABBITMQ_PASSWORD is None or RABBITMQ_USER is None or RABBITMQ_SERVER is None:
        print("no config, using localhost and guest/guest")
        RABBITMQ_SERVER='localhost'
        RABBITMQ_USER='guest'
        RABBITMQ_PASSWORD='guest'
    else:
        print ("aceepted rabbit, mode RABBITMQ")

while True:
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(RABBITMQ_SERVER,
                                       5672,
                                       '/',
                                       credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
#        channel.basic_qos(prefetch_count=1, global_qos=False)
        channel.queue_declare(queue='proxy')
        channel.basic_consume(queue='proxy', on_message_callback=callback, auto_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
#    except pika.exceptions.AMQPConnectionError:
#        print ("retry connecting to rabbit")
#        time.sleep(6)
    except Exception as e1:
        print (e1)
        print ("retry connecting to rabbit")
        time.sleep(6)
