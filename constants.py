from tyuiu import get_tyuiu_organizations

TOKEN: str = "5593955084:AAEdMLrGGVBXfcbyFB3Hhl0SRWhDU3qAmCw"

tyuiu_orgs = get_tyuiu_organizations()

edu_forms = {
  1: "Очная",
  2: "Заочная",
  3: "Очно-заочная",
}
edu_directions = {
  2: "Бюджет",
  1: "Договор",
}
edu_types = {
  1: "СПО (профессия)",
  2: "СПО (специальность)",
  3: "Бакалавриат",
  4: "Магистратура",
  5: "Специалитет",
  42: "Аспирантура",
}
