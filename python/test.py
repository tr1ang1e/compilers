def first():
    second()


def second():
    print("OK")


print(first.__name__)