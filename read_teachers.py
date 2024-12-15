from schedule.models import Teacher
import pandas as pd


def main():
    teachers_df = pd.read_csv('teacher_list.csv',
                               dtype=str, 
                               usecols=['擔任狀況', '主要所屬', '職責', '姓名', '性別', '所屬區'])
    print(teachers_df)



if __name__ == "__main__":
    main()