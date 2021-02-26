import utils
import settings
import time

def run():
    while True:
        utils.autoUnBlackOut()
        time.sleep(settings.alertDeamonIntervalMinutes * 60)

if __name__ == "__main__":
    run()