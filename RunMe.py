from time import sleep


class RunMe:
    count: int = 0

    def run(self, callback_function, is_shutting_down_function):
        print("RunMe.run(): Run called")
        while not is_shutting_down_function():
            sleep(1)
            self.count += 1
            print("RunMe.run(): Calling back with {}".format(self.count))
            callback_function(self.count)

        print("RunMe.run(): Shutting down, run returning")
