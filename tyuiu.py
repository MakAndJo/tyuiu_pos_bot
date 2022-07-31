from ctypes import Array
import re
from typing import List, Union
import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

TYUIU_URL = 'https://www.tyuiu.ru/wp-admin/admin-ajax.php'

TYUIU_HEADERES = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

TYUIU_EDUTYPE = {
  1: "профессия СПО", # среднее профессиональное образование (профессия) ⛔️
  2: "специальность СПО", # среднее профессиональное образование (специальность)⛔️
  3: "направление бакалавров", # бакалавриат ✅
  4: "направление магистров", # магистратура ⛔️
  5: "специальность ВО", # высшее образование (специалитет) ✅
  42: "Научная специальность", # аспирантура ⛔️
}

#second num
#spo1 01 t1 (college)
#spo2 02 t1 (college)
#baclor 03 t3 (institute)
#mag 04 t0 (institute)
#spec 05 t3 (institute)
#asp 1,2,3,4,5,6,7,8,9 t2 (institute)

TYUIU_EDUFORM = {
  1: "Очная",
  2: "Заочная",
  3: "Очно-заочная",
}

TYUIU_DIRECTION = {
  1: "Договор",
  2: "Бюджет",
}

TYUIU_PAYLOAD = {
  'action': 'rating',
  'ratingForm': 'org=4',
  'eduform': '1', # 1 - очные, 2 - заочные, 3 - очно-заочные
  'direction': '2', # 1 - договорные, 2 - бюджетные
  'competitionType': '0',
  'originals': '2',
  'prof': '21.05.02 Прикладная геология,  21.05.03 Технология геологической разведки'
}

cached_disciplines: Array[dict[str,any]] = []

def get_tyuiu_organizations() -> dict[int, str]:
  return ({
    1: "Институт дополнительного и дистанционного образования (Институт)",
    2: "Институт промышленных технологий и инжиниринга (Институт)",
    3: "Институт архитектуры и дизайна (Институт)",
    4: "Институт геологии и нефтегазодобычи (Институт)",
    5: "Институт транспорта (Институт)",
    6: "Строительный институт (Институт)",
    7: "Институт сервиса и отраслевого управления (Институт)",
    8: "Многопрофильный колледж (Колледж)",
    9: "филиал ТИУ в г. Сургуте (Филиал)",
    10: "филиал ТИУ в г. Нижневартовске (Филиал)",
    11: "филиал ТИУ в г. Ноябрьске (Филиал)",
    12: "филиал ТИУ в г. Тобольске (Филиал)",
    13: "Высшая инженерная школа EG"
  })

def get_tyuiu_disciplines(t_organization: int, eduform: int = 1, direction: int = 2, edutype: int = 2) -> list[str]:
  if len(cached_disciplines) > 0:
    for discipline in cached_disciplines:
      if discipline['organization'] == t_organization and discipline['eduform'] == eduform and discipline['direction'] == direction and discipline['edutype'] == edutype:
        return discipline['disciplines']
  tyuiu_payload = create_tyuiu_payload({
    'action': 'disciplines',
    'org': t_organization,
    'eduform': eduform,
    'direction': direction,
  }, True)
  data = get_tyuiu_data(tyuiu_payload)
  parsed_data = parse_tyuiu_data(data)
  disciplines = []
  if parsed_data.text != "0":
    for t_option in parsed_data.find_all('option'):
      if t_option.has_attr('value') and t_option.has_attr('name'):
        if t_option.get('name') == TYUIU_EDUTYPE[edutype]:
          disciplines.append(t_option.text)
    cached_disciplines.append({
      'organization': t_organization,
      'eduform': eduform,
      'direction': direction,
      'edutype': edutype,
      'disciplines': disciplines,
    })
  return disciplines


def create_tyuiu_payload(t_data: dict, strict = False) -> dict:
  if "direction" in t_data:
    if t_data["direction"] == "1":
      if "paid" in t_data:
        t_data["paid"] = "2" if t_data["paid"] else "1"
      else:
        t_data["paid"] = "1"
  if "originals" in t_data:
    t_data["originals"] = "2" if t_data["originals"] else "1"
  if "org" in t_data:
    t_data['ratingForm'] = 'org=' + str(t_data['org'])
  if not strict: return TYUIU_PAYLOAD | t_data
  else: return t_data

def get_tyuiu_data(t_payload: dict) -> Union[str, None]:
  try:
    response = requests.post(TYUIU_URL, data=t_payload, headers=TYUIU_HEADERES)
    return response.text
  except Exception as e:
    print(e)
    return None

def parse_tyuiu_data(t_html: str) -> Union[Tag, NavigableString, None]:
  try:
    t_parsed_html = BeautifulSoup(t_html, features='html.parser')
    for element in t_parsed_html(text=lambda text: isinstance(text, Comment)):
      element.extract()
    return t_parsed_html
  except Exception as e:
    print(e)
    return None

def parse_tyuiu_table_to_array(t_table: Union[Tag, NavigableString, None], add_header=True) -> List[Union[List, dict]]:

  def normalize_headings(headings):
    headings = []
    for heading in headings[0]:
      if heading.has_attr('colspan'):
        headings.extend(headings[1])
      else:
        headings.append(heading)
    return headings

  t_results = []
  headings_1 = []
  headings_2 = []

  for t_data in t_table.find_all('tr'):
    if t_data.find('th'):
      for heading in t_data.find_all('th'):
        if heading.has_attr('colspan') or heading.has_attr('rowspan'):
          headings_1.append(heading)
        else:
          headings_2.append(heading)
    elif t_data.find('tr'):
      for row in t_data.find_all('tr'):
        t_result = []
        for td in row.find_all('td'):
          t_result.append(td.text)
        t_results.append(t_result)

  end_results = []
  if add_header:
    headings = normalize_headings([headings_1, headings_2])
    heads = [heading.text for heading in headings]
    for t_result in t_results:
      dictionary = dict()
      for index, name in enumerate(heads):
        dictionary[name] = t_result[index]
      end_results.append(dictionary)
  else:
    end_results.extend(t_results)
  return end_results

def parse_discipline_edutype(discipline: str) -> int:
  d_type = str(discipline).split('.')[1]
  if len(d_type) == 1: return 42 # asp
  if d_type == "01": return 1 #spo prof
  if d_type == "02": return 2 #spo spec
  if d_type == "03": return 3 #bak
  if d_type == "04": return 4 #mag
  if d_type == "05": return 5 #spec vo
  return 0


def get_tyuiu_results(payload: dict, mark: int, with_originals: bool = False) -> List[dict]:
  end_result = dict()
  tyuiu_payload = create_tyuiu_payload(payload | {
    'originals': with_originals,
  })
  data = get_tyuiu_data(tyuiu_payload)
  parsed_data = parse_tyuiu_data(data)
  if parsed_data:
    end_result['prof'] = payload['prof']
    end_result['org'] = payload['org']
    end_result['direction'] = int(payload['direction'])
    end_result['eduform'] = int(payload['eduform'])
    end_result['edutype'] = parse_discipline_edutype(payload['prof'])

    if end_result['direction'] == 2: # budget
      if end_result['edutype'] == 1: # spo prof
        profspo_count = parsed_data.find('div', id=re.compile('^enrolled_profspo_count'))
        end_result['budget_count'] = int(profspo_count.text)
      elif end_result['edutype'] == 2: # spo spec
        specspo_count = parsed_data.find('div', id=re.compile('^enrolled_specspo_count'))
        end_result['budget_count'] = int(specspo_count.text)
      elif end_result['edutype'] == 3 or end_result['edutype'] == 5: # bak or spec vo
        bak_count = parsed_data.find('div', id=re.compile('^enrolled_bak_count'))
        end_result['budget_count'] = int(bak_count.text)
      elif end_result['edutype'] == 4: # mag
        mag_count = parsed_data.find('div', id=re.compile('^enrolled_mag_count'))
        end_result['budget_count'] = int(mag_count.text)
      else:
        end_result['budget_count'] = 0
    else: #paid
      end_result['budget_count'] = 0

    table = parsed_data.find('table', attrs={'id':'table'})
    results = parse_tyuiu_table_to_array(table, add_header=False)

    if len(results) != 0:
      t_pos = 0
      t_total = int(mark)
      for index, result in enumerate(results):
        pos = int(result[0])
        comp_type = str(result[9])
        if comp_type == "Общий конкурс":
          total = int(result[7])
          if total <= int(mark):
            t_pos = pos
            t_total = total
            break
        t_pos = pos + 1
      end_result['pos'] = t_pos
      end_result['total'] = t_total
  return end_result
    



def main():

  def is_digit(digit: str) -> bool:
    return str(digit).isdigit()

  def is_valid_w_bool(word: str) -> bool:
    word = word.lower()
    return (str(word).startswith("д") or str(word).startswith("н")) or (str(word).startswith("y") or str(word).startswith("n"))

  def parse_w_bool(word: str) -> bool:
    word = word.lower()
    if str(word).startswith("д") or str(word).startswith("y"):
      return True
    elif str(word).startswith("н") or str(word).startswith("n"):
      return False
    return None
  
  needed_payloads = [
    {
      'org': 2,
      'prof': '13.03.02 Электроэнергетика и электротехника (Электроснабжение; Электропривод и автоматика)'
    },
    {
      'org': 2,
      'prof': '15.03.06 Мехатроника и робототехника (Робототехника и гибкие производственные модули)'
    },
    {
      'org': 4,
      'prof': '21.05.02 Прикладная геология,  21.05.03 Технология геологической разведки'
    },
    {
      'org': 4,
      'prof': '27.03.04 Управление в технических системах (Интеллектуальные системы и средства АУ)'
    },
    {
      'org': 4,
      'prof': '09.03.01 Информатика и вычислительная техника  (АСОИУ), 09.03.02 Информационные системы и технологии (ИСТГНГО, ИИП)'
    },
    {
      'org': 5,
      'prof': '23.05.01 Наземные транспортно-технологические средства (Подъемно-транспортные, строительные, дорожные средства и оборудование)'
    },
    {
      'org': 6,
      'prof': '09.03.02 Информационные системы и технологии (Информационные системы и технологии)'
    },
    {
      'org': 7,
      'prof': '01.03.02 Прикладная математика и информатика'
    },
    {
      'org': 7,
      'prof': '02.03.01 Математика и компьютерные науки'
    }
  ]

  def run():
    print("\033[H\033[J", end="") # clear the screen

    while True:
      word: str = input('Введите своё количество баллов: [100-300]\xa0').lower()
      if not is_digit(word) or int(word) > 300 or int(word) < 100: # if not exam mark
        print("Введите баллы от 100 до 300!")
      else: 
        mark = int(word)
        break

    while True:
      word: str = input('С оригиналами? [Д/н]\xa0').lower()
      if not is_valid_w_bool(word): # if not exam mark
        print("Введите да или нет!")
      else: 
        originals = parse_w_bool(word)
        break

    for indx, payload in enumerate(needed_payloads):

      print("\n")

      res = get_tyuiu_results(payload, mark, originals)
      
      print(f"Профессия: {res['prof']}")

      print(f"Общее количество бюджетных мест: {res['bak_count']}")

      if "pos" in res:
        print(f"Ваша позиция в списке: {res['pos']} ({res['total']} баллов)")
      else:
        print("Ваша позиция в списке: не найдена")
  
  run()
  return False


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    pass
else:
  print("Import tyuiu:", __name__)

