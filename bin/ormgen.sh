# generate sqlalchemy Class file from existing mysql DB and tables
sqlacodegen --tables task --outfile taskORM.py mysql+pymysql://vtcdb:vtcdb@localhost:3306/appgw?charset=utf8
sqlacodegen --tables service --outfile serviceORM.py mysql+pymysql://vtcdb:vtcdb@localhost:3306/appgw?charset=utf8
sqlacodegen --tables provider --outfile providerORM.py mysql+pymysql://vtcdb:vtcdb@localhost:3306/appgw?charset=utf8
