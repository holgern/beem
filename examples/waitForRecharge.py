from win10toast import ToastNotifier
from beem.account import Account
import time

if __name__ == "__main__":
    toaster = ToastNotifier()

    randowhale = Account("randowhale")
    randowhale.refresh()

    try:
        while True:
            time.sleep(15)
            randowhale.refresh()
            if randowhale.profile["name"] == "Rando Is Sleeping":
                # print(randowhale)
                print("still sleeping, awake in " + randowhale.get_recharge_time_str(99))
            else:
                toaster.show_toast(randowhale.profile["name"],
                                   randowhale.profile["about"],
                                   icon_path=None,
                                   duration=5,
                                   threaded=True)
                # Wait for threaded notification to finish
                while toaster.notification_active():
                    time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    # Wait for threaded notification to finish
    while toaster.notification_active():
        time.sleep(0.1)
