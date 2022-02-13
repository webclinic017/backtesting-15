import pandas as pd
import numpy as np
import empyrical as emp
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import seaborn as sns

import datetime
from main import Config

# initialise the global var
metavar = Config()

# initialise pyplot settings
plt.rcParams["axes.unicode_minus"] = False  # display minus sign correctly
plt.rcParams["font.family"] = ["Heiti TC"]  # for Chinese characters


class Microscope:
    # Reproduce intuitive plots for timeseries data analysis
    figsize = (12, 8)

    def __init__(self, results_df: pd.DataFrame, prices_df: pd.DataFrame, opt_df: pd.DataFrame):
        """
        Params
        ------
        results_df: Timereturn dataframe from the backtest programe
        prices_df: Dataframe of the underlying asset's adj close
        opt_df: Dataframe of the optimised results

        Attributes
        ----------
        - timereturn:
        - detailed_rets:
        - ann_rets:
        - month_rets:
        - cumrets:
        - drawdown:
        """
        # essential attributes
        self.timereturn = results_df
        self.detailed_rets = self.sep_month_and_year(self.timereturn)
        self.opt_df = opt_df

        # 年化和月化收益率
        self.ann_rets, self.ann_mean = self.cal_annual_rets(self.detailed_rets)
        self.month_rets = self.cal_monthly_rets(self.detailed_rets)

        # 净值和回撤
        self.cumrets = emp.cum_returns(self.timereturn['timereturn'], starting_value=1.0)
        maxrets = self.cumrets.cummax()
        self.drawdown = (self.cumrets - maxrets) / maxrets
        self.ann_mdd, self.calmar = self.cal_annual_mdd_calmar(self.detailed_rets)
        
        # 标的历史价格
        self.prices_df = self.normalise_prices(self.timereturn, prices_df)

    def normalise_prices(self, timereturn, prices_df, starting_value=1):
        """
        Normalise the prices dataframe starting from 1 in order to
        compare the trend between prices and cumrets over the same timeframe

        Params
        ------
        timereturn: Timereturn dataframe from the backtesting programe
        prices_df: Dataframe of the underlying asset's adj.close

        Retruns
        -------
        prices_df: Prices dataframe with the same timeframe
        """
        fromdate, todate = timereturn.index[0].date().isoformat(), timereturn.index[-1].date().isoformat()
        prices_df = prices_df.loc[fromdate:todate]['S_DQ_ADJCLOSE']
        prices_df = (prices_df.pct_change().fillna(0) + 1).cumprod()

        return prices_df
        
    def sep_month_and_year(self, df):
        df['year'] = df.index.year
        df['month'] = df.index.month
        
        return df
    
    def cal_annual_rets(self, df):
        """
        Convert minute timereturn to annual returns

        Params
        ------
        df: Timereturn dataframe in minutes basis

        Returns
        -------
        ann_rets: Annual timereturn dataframe
        ann_mean: Mean value of the annual return
        """
        years = df['year'].unique()
        ann_rets = {}

        # scale the min returns to annual return
        for year in years:
            # year_summary = df[df['year'] == year].describe()['timereturn']
            # ann_rets[year] = year_summary['mean'] * year_summary['count']
            min_rets = df[df['year'] == year]['timereturn']
            ann_rets[year] = emp.cum_returns_final(min_rets, starting_value=1) - 1  # (1 + rets) ** (1 / num_year) - 1

        ann_rets = pd.Series(ann_rets)
        ann_mean = ann_rets.mean()
        
        return ann_rets, ann_mean

    def cal_annual_mdd_calmar(self, df):
        """
        Calculate the maximum drawdown and calmar ratio
        for each year's return

        Params
        ------
        df: Timereturn dataframe in minutes basis

        Returns
        -------
        ann_mdd: Annual maximum drawdown level
        ann_calmar: Annual calmar raito
        """
        years = df['year'].unique()
        ann_mdd = {} 
        ann_calmar = {}

        for year in years:
            min_rets = df[df['year'] == year]['timereturn']
            ann_rets = emp.cum_returns_final(min_rets, starting_value=1) - 1
            ann_mdd[year] = emp.max_drawdown(min_rets)
            ann_calmar[year] = ann_rets / -ann_mdd[year]

        ann_mdd = pd.Series(ann_mdd)
        ann_calmar = pd.Series(ann_calmar)

        return ann_mdd, ann_calmar
    
    def cal_monthly_rets(self, df):
        """
        Convert timereturn dataframe in minutes to montly basis

        Params
        ------
        df: Timereturn dataframe in minutes basis

        Returns
        -------
        monthly_rets: Monthly timereturn dataframe
        """
        years = df['year'].unique()
        monthly_rets = pd.DataFrame(columns=df['year'].unique(), index=range(1, 13))

        for year in years:
            year_df = df[df['year'] == year]
            months = year_df['month'].unique()
            
            # scale the min returns to monthly returns
            for month in months:
                min_rets = year_df[year_df['month'] == month]['timereturn']
                rets = emp.cum_returns_final(min_rets, starting_value=1) - 1  # (1 + rets) ** (1 / num_month) - 1
                monthly_rets.loc[month,year] = rets

        monthly_rets = monthly_rets.astype(float).T
        monthly_rets = monthly_rets.replace(np.nan, 0)

        return monthly_rets
        
    def plot_annrets_mdd_calmar(self, ann_rets, ann_mean, ann_mdd, ann_calmar):
        """
        Create a combination of bar chart and line chart that
        illustrate the annual return, max drawdown and calmar
        ratio for each year backtesting
        
        Params
        ------
        ann_rets: Timereturn dataframe in annual basis
        ann_mean: Mean return across the timeframe
        ann_mdd: Annual maximum drawdown
        ann_calmar: Annual calmar ratio

        Returns
        -------
        bar chart for annual returns
        """
        fig, ax1 = plt.subplots(figsize=self.figsize)
        ax1 = sns.barplot(
            x=ann_mdd.index, y=ann_mdd.values,
            color='brown', capsize=0.3, label='最大回撤'
        )

        ax2 = ax1.twinx()
        ax2.plot(
                ax1.get_xticks(), ann_calmar.values,
                color='tab:green', label='收益回撤比',
                marker='o', linewidth=3
                )
        
        ax3 = ax3 = sns.barplot(
            x=ann_rets.index, y=ann_rets.values,
            color='tab:blue', capsize=0.3,
            ax=ax1, label='年化收益率'
        )

        # average line
        ax3.axhline(ann_mean, alpha=0.8, linewidth=4,
                   dashes=(5, 2), color='black', label=f'平均值 {ann_mean:.2%}')
        
        # solid line in the x axis
        ax3.axhline(0, color='black')
        
        # set axis labels
        ax1.set_xlabel('年份')
        ax1.set_ylabel('最大回撤')
        ax2.set_ylabel('收益回撤比')
        ax3.set_ylabel('收益率')

        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        h3, l3 = ax3.get_legend_handles_labels()

        # format y axis to percentage style
        ax1.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

        plt.legend(h1 + h2, l1 + l2, fontsize=12, loc='upper right')
        plt.title('年化收益率', fontsize=14)
        fig.tight_layout()

        plt.savefig(f'./images/{metavar.contract}rets_mdd_calmar.png')
        plt.show()

    def plot_month_rets_heatmap(self, monthly_rets):
        """
        Plot the monthly return for each year in heatmap

        Params
        ------
        monthly_rets: Monthly timereturn dataframe

        Returns
        -------
        Heatmap of monthly return
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        values = monthly_rets.values  # np.array of the monthly returns

        ax = sns.heatmap(monthly_rets, cmap='Blues', cbar=True)

        # make sure the annot is in the center of the block
        # while also in a percentage format
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                # do not display the nan in annot
                if values[i, j] != 0:
                    text = ax.text(j + 0.5, i + 0.5, f"{values[i, j]:.2%}",
                                    ha='center', va='center', color="black")

        ax.set_ylabel('年份')
        ax.set_xlabel('月份')
        plt.title('月度收益率', fontsize=14)
        fig.tight_layout()

        plt.savefig(f'./images/{metavar.contract}month_rets_heatmap.png')
        plt.show()

    def plot_cumrets_dd_prices(self, cumrets, dd, prices):
        """
        Plot a line graph that shows the trends among cumulative returns,
        drawdown and the underlying's prices over the whole period
        
        Params
        ------
        cumrets: pd.DataFrame of the cumulative returns
        dd: pd.DataFrame of the return drawdown
        prices: pd.DataFrame of the underlying asset's ADJCLOSE
        
        Returns
        -------
        Line graph of params trends over the timeframe 
        """
        fig, ax1 = plt.subplots(figsize=self.figsize, sharex=True)
        
        # cumulative returns
        ax1 = cumrets.plot(rot=45, grid=False, label="净值曲线", color="brown", linewidth=2)
        ax1 = prices.plot(
                grid=False, label='价格曲线',
                alpha=0.7, color='grey', linewidth=2,
                )
        # ax1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 6)))
        # ax1.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))

        # drawdown and prices
        ax2 = ax1.twinx()
        ax2 = dd.plot.area(grid=False, label="回撤情况", alpha=0.3, color="tab:blue", linewidth=1)

        ax1.yaxis.set_ticks_position("left")
        ax2.yaxis.set_ticks_position("right")

        ax1.set_xlabel("日期")
        ax1.set_ylabel("净值")
        # ax2.set_ylabel('回撤情况')
        # ax3.set_ylabel('价格曲线')

        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()

        plt.legend(h1 + h2, l1 + l2, fontsize=12, ncol=1, loc="upper right")
        plt.title(f"{metavar.contract}回测结果")
        plt.margins(x=0)
        fig.tight_layout()

        plt.savefig(f'./images/{metavar.contract}rets_dd_prices.png')
        plt.show()

    def plot_opt_results(self, df):
        """
        Bar chart compares the annual returns, calmar ratio
        and the sharpe ratio for different parameters
        """
        plt.style.use('seaborn')

        fig, ax = plt.subplots(figsize=self.figsize)
        df.plot(
                kind='bar', x='period', y=['ann_rets', 'max_drawdown'],
                ax=ax, rot=0, title='Performance for Different Lookback Period'
                )

        ax.axhline(0, color='black', linewidth=0.2)

        plt.grid(False)
        plt.savefig('./images/params_performance.png')
        fig.tight_layout()
        plt.show()


if __name__ == '__main__':
    rets_file = "./results/timereturn.csv"
    opt_results_path = "./results/opt_results.csv"

    rets_df = pd.read_csv(rets_file)
    rets_df = rets_df.rename(columns={'Unnamed: 0': 'Date', '0': 'timereturn'})
    rets_df.set_index('Date', inplace=True)
    rets_df.index = pd.to_datetime(rets_df.index)
    prices_df = metavar.test_df.loc[metavar.fromdate:metavar.todate]

    opt_df = pd.read_csv(opt_results_path)  # 参数寻优

    ind = Microscope(rets_df, prices_df, opt_df)
    
    # calculate annually and monthly returns
    ann_rets, ann_mean = ind.ann_rets, ind.ann_mean
    monthly_rets = ind.month_rets

    # calculate annually max_drawdown and calmar ratio
    ann_mdd, ann_calmar = ind.ann_mdd, ind.calmar

    # plot the bar chart and heatmap
    ind.plot_annrets_mdd_calmar(ann_rets, ann_mean, ann_mdd, ann_calmar)
    ind.plot_month_rets_heatmap(monthly_rets)
    ind.plot_cumrets_dd_prices(ind.cumrets, ind.drawdown, ind.prices_df)
    ind.plot_opt_results(ind.opt_df)

