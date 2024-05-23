import pika
import sys
import os
import json
import subprocess
import logging

logger = logging.getLogger(__name__)


def main():
    print("starting marker service")
    try:
        rabbitconn = pika.BlockingConnection(
            pika.ConnectionParameters('rabbitmq'))
        print("rabbit connection made")
    except Exception as e:
        print(e)
        sys.exit(0)

    seen = {}

    channel = rabbitconn.channel()
    channel.queue_declare(queue='parse_pdf')
    print("connected to 'pdf_parse' channel")

    def callback(ch, method, properties, body):
        try:
            payload = json.loads(body)
            print(f" [x] Received {payload}")
            in_path = payload['in_path']
            out_path = payload['out_path']
            pid = payload['id']
            if pid in seen.keys():
                seen[pid] += 1
            else:
                seen[pid] = 0
            if seen[pid] > 2:
                print(f' [!] Skipping payload with id {pid}')
            elif payload['status'] is "processing":
                pass
            else:
                try:
                    payload['status'] = "processing"
                    channel.basic_publish(exchange='',
                                          routing_key='parse_pdf',
                                          body=json.dumps(payload))

                    subprocess.run([
                        "python",
                        "convert_single.py",
                        f'{in_path}',
                        f'{out_path}',
                        "--max_pages",
                        "2",
                        "--batch_multiplier",
                        "2",
                        "--langs",
                        "English"
                    ])
                except Exception as e:
                    print(json.dumps(payload, indent=4))
                    print(f"Error peocessing pdf with id {pid}")
                    print(e)
                    payload['status'] = "error"
                    channel.basic_publish(exchange='',
                                          routing_key='parse_pdf',
                                          body=json.dumps(payload))
        except Exception as e:
            print(e)

    channel.basic_consume(queue='parse_pdf',
                          auto_ack=True,
                          on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    finally:
        sys.exit(0)
