class Enter(object):
    def int(input_descripton, arg_error, arg_min, arg_max, arg_isnt):
        while True:
            try:
                i = int(input(input_descripton))
                if Enter.arg_min_f(i, arg_min) is False or Enter.arg_max_f(i, arg_max) is False or Enter.arg_isnt_f(i, arg_isnt) is False:
                    print(arg_error)
                    continue
                return i
            except:
                print(arg_error)
                continue

    def float(input_descripton, arg_error, arg_min, arg_max, arg_isnt_in_list):
        while True:
            try:
                i = float(input(input_descripton))
                if Enter.arg_min_f(i, arg_min) is False or Enter.arg_max_f(i, arg_max) is False or Enter.arg_isnt_in_list_f(i, arg_isnt_in_list) is False:
                    print(arg_error)
                    continue
                return i
            except:
                print(arg_error)
                continue

    def str(input_descripton, arg_error, arg_min, arg_max, arg_isnt_in_list):
        while True:
            try:
                i = str(input(input_descripton))
                if Enter.arg_min_f(i, arg_min) is False or Enter.arg_max_f(i, arg_max) is False or Enter.arg_isnt_in_list_f(i, arg_isnt_in_list) is False:
                    print(arg_error)
                    continue
                return i
            except:
                print(arg_error)
                continue
    def arg_min_f(i, arg):
        if arg is not None:
            if i < arg:
                return False
        else:
            return True

    def arg_max_f(i, arg):
        if arg is not None:
            if i > arg:
                return False
        else:
            return True

    def arg_isnt_f(i, arg):
        if arg is not None:
            if i == arg or arg is True:
                return False
        else:
            return True

    def arg_isnt_in_list_f(i, arg):
        if arg is not None:
            if isinstance(arg, (list, tuple)):
                for el in arg:
                    if el == i:
                        return False
            elif i == arg or arg is True:
                return False
        else:
            return True

class Digits_operator(object):
    def find_number_of_digits(dgt):
        dgt = abs(dgt)
        counter = 0
        if dgt <= 0:
            return counter
        else:
            counter += 1
            return Digits_operator.find_number_of_digits(dgt // 10)

    def find_digits_and_print_them_out(dgt, lst):
        dgt = abs(int(dgt))
        lst = list(lst)
        if dgt <= 0:
            return lst
        else:
            lst.append(int(dgt % 10))
            return Digits_operator.find_digits_and_print_them_out(dgt // 10, lst)

class Trimmer(object):
    def left(string, amount):
        return string[:amount]

    def right(string, amount):
        return string[-amount:]