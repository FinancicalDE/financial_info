import os
from yahooquery import Ticker
from financial_etl.base import Base_ETL
import pandas as pd

class IncomeStatement_ETL(Base_ETL):

    def __init__(self):
        super().__init__()
        self._username = os.getenv('YFINANCE_USER')
        self._password = os.getenv('YFINANCE_PASSWORD')

        self.columns_to_keep = ['symbol', 'date', 'TotalRevenue', 'SpecialIncomeCharges',
                   'PretaxIncome', 'TaxProvision', 'NetIncome', 'NetIncomeCommonStockholders',
                   'DilutedNIAvailtoComStockholders', 'BasicEPS', 'DilutedEPS',
                   'BasicAverageShares', 'DilutedAverageShares', 'InterestIncome',
                   'NetIncomeFromContinuingAndDiscontinuedOperation', 'NormalizedIncome',
                   'ReconciledDepreciation', 'NetIncomeFromContinuingOperationNetMinorityInterest',
                   'TotalUnusualItemsExcludingGoodwill', 'TotalUnusualItems', 'TaxRateForCalcs',
                   'TaxEffectOfUnusualItems'
                  ]

    def extract(self, symbols, filename_out=None):
        '''Extract Income Statement with Yfianace API

            Args:
                symbols = ['JPM', 'GS', 'MS', 'SIVBQ']

            Returns:
                pd.DataFrame
        '''

        raw_data = Ticker(symbols=symbols, username=self._username, password=self._password).p_income_statement(trailing=False, frequency='q')

        if filename_out is None:
            if not os.path.exists(self.dir_data_lake):
                os.makedirs(self.dir_data_lake)

            filename_out = os.path.join(self.dir_data_lake, 'income_statement.csv')

        raw_data.to_csv(filename_out, index=True)
        object_key = 's3://lg18dagbucket/STAGING/income_statement.csv'

        self._save_data_in_s3(filename_out, object_key)

    def _rename_columns(self, df, column_rename_mapping={'asOfDate': 'date'}):
        return df.rename(columns=column_rename_mapping)

    def _filter_by_date_range(self, df, date_range):
        df['date'] = pd.to_datetime(df['date'])
        df = df.loc[df['date'].isin(pd.date_range(start=date_range[0], end=date_range[1]))]
        return df.reset_index(drop=True)

    def transform(self, filename_in, filename_out, save_mode='parquet'):

        df_raw = pd.read_csv(filename_in)

        df = self._rename_columns(df_raw, column_rename_mapping={'asOfDate': 'date'})

        df = self._filter_by_date_range(df, date_range=['2017-01-01', '2022-03-31'])

        df = df[self.columns_to_keep]

        if save_mode == 'parquet':
            df.to_parquet(filename_out)
            object_key = 's3://lg18dagbucket/to_warehouse/income_statement_cleaned.parquet'
            self._save_data_in_s3(filename_out, object_key)

        elif save_mode == 'csv':
            df.to_csv(filename_out, index=False)
            object_key = 's3://lg18dagbucket/to_warehouse/income_statement_cleaned.csv'
            self._save_data_in_s3(filename_out, object_key)

        return df
