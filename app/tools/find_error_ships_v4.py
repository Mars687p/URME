from typing import Union

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag


def parse_file(soup: BeautifulSoup,
               ident: str) -> Union[ResultSet, list[ResultSet[Tag]], None]:
    boxes: Union[ResultSet, list[ResultSet[Tag]]] = []
    positions: ResultSet[Tag] = soup.find_all('wb:Position')
    for position in positions:
        identity = position.find('wb:Identity')
        if identity is None:
            return None

        if ident == '':
            boxes.append(position.find_all('ce:boxpos'))
            continue

        if identity.text == ident:
            boxes = position.find_all('ce:boxpos')
            break
    return boxes


def check_position(boxes: ResultSet) -> int:
    len_fsm_in_pos: int = 0
    for box in boxes:
        fsm_in_box: list[Tag] = []
        len_fsm: int = 0
        if type(box) is Tag:
            fsm_in_box = box.find_all('ce:amc')
            len_fsm = len(fsm_in_box)
            if len_fsm not in [6, 9, 12, 24, 30]:
                num_box = box.find('ce:boxnumber')
                if num_box is None:
                    raise TypeError
                print(f"Не полный короб: {num_box.text}")

        for fsm in fsm_in_box:
            if len(fsm.text) < 150:
                print(f"Не корректная длина ФСМ({len(fsm.text)}): {fsm.text}")
        len_fsm_in_pos += len_fsm
    return len_fsm_in_pos


def start(path_file: bytes, ident: str = '') -> None:
    with open(path_file,
              'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml-xml')

    boxes = parse_file(soup, ident)
    if boxes is None:
        print('Позиции не найдены')
        return

    all_fsm: int = 0
    if type(boxes) is ResultSet:
        len_fsm = check_position(boxes)
        all_fsm += len_fsm
    elif type(boxes) is list:
        for item in boxes:
            len_fsm = check_position(item)
            all_fsm += len_fsm
    print(f"Всего ФСМ: {all_fsm}")


if __name__ == '__main__':
    identity = input('Укажите позицию или оставьте поле пустым: ')
    path_file = input('Укажите полный путь к файлу: ')
    start(path_file.encode('unicode_escape'), identity)
