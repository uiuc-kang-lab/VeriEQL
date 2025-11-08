# -*- coding: utf-8 -*-

from constants import DIALECT
from environment import Environment


def main(sql1, sql2, schema, ROW_NUM=2, constraints=None, **kwargs):
    with Environment(**kwargs) as env:
        for k, v in schema.items():
            env.create_database(attributes=v, bound_size=ROW_NUM, name=k)
        env.add_constraints(constraints)
        env.save_checkpoints()
        if env._script_writer is not None:
            env._script_writer.save_checkpoints()
        result = env.analyze(sql1, sql2, out_file="test/test.py")
        if env.show_counterexample:
            print(env.counterexample)
        if env.traversing_time is not None:
            print(f"Time cost: {env.traversing_time + env.solving_time:.2f}")
        if result == True:
            print("\033[1;32;40m>>> Equivalent! \033[0m")
        else:
            print("\033[1;31;40m>>> Non-Equivalent! Found a counterexample! \033[0m")


if __name__ == '__main__':
    sql1, sql2 = [
        "SELECT DISTINCT PAGE_ID AS RECOMMENDED_PAGE FROM (SELECT CASE WHEN USER1_ID=1 THEN USER2_ID WHEN USER2_ID=1 THEN USER1_ID ELSE NULL END AS USER_ID FROM FRIENDSHIP) AS TB1 JOIN LIKES AS TB2 ON TB1.USER_ID=TB2.USER_ID WHERE PAGE_ID NOT IN (SELECT PAGE_ID FROM LIKES WHERE USER_ID=1)",
        "WITH USER1_FRIEND AS ( SELECT DISTINCT USER1_ID AS SELF_ID, USER2_ID AS FRIEND_ID FROM FRIENDSHIP WHERE USER1_ID = 1 UNION ALL SELECT DISTINCT USER2_ID AS SELF_ID, USER1_ID AS FRIEND_ID FROM FRIENDSHIP WHERE USER2_ID = 1 ) ,TMP1 AS (SELECT T1.SELF_ID, T2.PAGE_ID AS SELF_LIKE FROM USER1_FRIEND T1 LEFT JOIN LIKES T2 ON T1.SELF_ID = T2.USER_ID GROUP BY 1,2), TMP2 AS (SELECT T1.SELF_ID, T3.PAGE_ID AS FRIEND_LIKE FROM USER1_FRIEND T1 LEFT JOIN LIKES T3 ON T1.FRIEND_ID = T3.USER_ID GROUP BY 1,2), TMP3 AS (SELECT TMP1.SELF_ID, IFNULL(TMP1.SELF_LIKE,0) AS SELF_LIKE, IFNULL(TMP2.FRIEND_LIKE,0) AS FRIEND_LIKE FROM TMP1 LEFT JOIN TMP2 ON TMP1.SELF_ID = TMP2.SELF_ID) SELECT DISTINCT (FRIEND_LIKE) AS RECOMMENDED_PAGE FROM TMP3 WHERE FRIEND_LIKE NOT IN (SELECT DISTINCT SELF_LIKE FROM TMP3) AND FRIEND_LIKE <> 0 ORDER BY 1 DESC"
    ]
    # FRIENDSHIP: (USER1_ID, USER2_ID) [PK]
    # LIKES: (USER_ID, PAGE_ID) [PK]
    schema = {'FRIENDSHIP': {'USER1_ID': 'INT', 'USER2_ID': 'INT'}, 'LIKES': {'USER_ID': 'INT', 'PAGE_ID': 'INT'}}
    constraints = [{'primary': [{'value': 'FRIENDSHIP__USER1_ID'}, {'value': 'FRIENDSHIP__USER2_ID'}]},
                   {'primary': [{'value': 'LIKES__USER_ID'}, {'value': 'LIKES__PAGE_ID'}]},
                   {'neq': [{'value': 'FRIENDSHIP__USER1_ID'}, {'value': 'FRIENDSHIP__USER2_ID'}]}]
    bound_size = 1
    # generate_code: generate SQL code and running outputs if you find a counterexample
    # timer: show time costs
    # show_counterexample: print counterexample
    config = {'generate_code': True, 'timer': True, 'show_counterexample': True, "dialect": DIALECT.MYSQL}
    main(sql1, sql2, schema, ROW_NUM=bound_size, constraints=constraints, **config)
