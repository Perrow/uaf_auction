# coding=utf-8


class ListShorter:

    def __init__(self):
        pass

    def short(self, data):

        """
        Removes consecutive elements from list of intergers and replaces the removed items with a dash and returns a string. eg [1, 2, 3, 4, 6] -> "1-4, 6"
        :param data: list of integers
        :return: string with following elemets replaced with a dash
        """
        start = data[0]
        result = []
        count = 0
        end = None
        for current in data:
            if start == current:
                result.append(start)
            elif start + count == current:
                end = current
            else:
                if end:
                    result.append("-")
                    result.append(end)
                    end = None
                result.append(current)
                start = current
                count = 0
            count += 1

        if end:
            result.append("-")
            result.append(end)

        old = None
        in_dash = False
        new_result = []
        for index, current in enumerate(result):
            if current == "-":
                in_dash = True

            if current != "-" and not in_dash:
                if old:
                    new_result.append("{}".format(old))
                old = current

            if current != "-" and in_dash:
                new_result.append("{}-{}".format(old, current))
                in_dash = False
                old = None

        return (", ".join(new_result))