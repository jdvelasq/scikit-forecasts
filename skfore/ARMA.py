"""

ARMA Model
===============================================================================

Overview
-------------------------------------------------------------------------------

This module contains ARMA models using SciPy's minimization method.

Examples
-------------------------------------------------------------------------------


>>> ts = pandas.Series.from_csv('../datasets/champagne.csv', index_col = 0, header = 0)
>>> model = ARMA(p = 2, q = 3)
>>> model = model.fit(ts)
>>> fitted_model = model.predict(ts)
>>> prediction = model.forecast(ts, periods = 3)
>>> prediction
            ci_inf  ci_sup       series
1972-10-01     NaN     NaN  3646.138084
1972-11-01     NaN     NaN  4763.476525
1972-12-01     NaN     NaN  4205.279228
>>> prediction = model.forecast(ts, periods = 2, confidence_interval = 0.95)
>>> prediction
                ci_inf       ci_sup       series
1972-10-01   80.935482  6479.458676  3645.453875
1972-11-01  733.457614  8092.782317  4762.201208

"""

from skfore.base_model import base_model

import numpy
import scipy
import pandas
from sklearn import *
from skfore.extras import add_next_date

class ARMA(base_model):
    """ Moving-average model
    
    Parameter optimization method: scipy's minimization

    Args:
        p (int): AR order
        q (int): MA order

    Returns:
        ARMA model structure of order q.

    """

    def __init__(self, p=None, q=None, intercept=None, phi=None, theta=None):
        self.y = None
        
        if p == None:
            raise ValueError('Please insert parameter p')
        else:
            self.p = p
        
        if q == None:
            raise ValueError('Please insert parameter q')
        else:
            self.q = q
        
        if intercept == None:
            self.intercept = None
        elif intercept == False:
            self.intercept = 0
        else:
            self.intercept = intercept
        
        if phi == None:
            self.phi = None
        else:
            self.phi = phi
            
        if theta == None:
            self.theta = None
        else:
            self.theta = theta
            
        if intercept == None and theta == None and phi == None:
            self.optim_type = 'complete'
        elif intercept == None and theta != None and phi != None:
            self.optim_type = 'optim_intercept'
        elif intercept == False and theta == None and phi == None:
            self.optim_type = 'no_intercept'
        elif intercept != None and theta == None and phi == None:
            self.optim_type = 'optim_params'
        elif intercept != None and theta != None and phi != None:
            self.optim_type = 'no_optim'
        else:
            raise ValueError('Please fulfill all parameters')
            
        
    def __repr__(self):
        return 'ARMA(p = ' + str(self.p) + ', q = ' + str(self.q) + ', intercept = ' + str(self.intercept) + ', phi = ' + str(self.phi) + ', theta = ' + str(self.theta) +')'
        

    def params2vector(self):
        """ Parameters to vector
        
        Args:
            None.
            
        Returns:
            Vector parameters of length p+1 to use in optimization.

        """        
        params = list()
        if self.intercept == None:
            self.intercept = numpy.random.rand(1)[0]
        if self.phi == None:
            self.phi = numpy.random.rand(self.p)
        if self.theta == None:
            self.theta = numpy.random.rand(self.q)
        
        if self.optim_type == 'complete':
            params.append(self.intercept)
            for i in range(len(self.phi)):
                params.append(self.phi[i])
            for i in range(len(self.theta)):
                params.append(self.theta[i])
            return params
        elif self.optim_type == 'no_intercept' or self.optim_type == 'optim_params':
            for i in range(len(self.phi)):
                params.append(self.phi[i])
            for i in range(len(self.theta)):
                params.append(self.theta[i])
            return params
        elif self.optim_type == 'optim_intercept':
            params.append(self.intercept)
            return params
        elif self.optim_type == 'no_optim':
            pass
        

    def vector2params(self, vector):
        """ Vector to parameters
        
        Args:
            
        Returns:
            self

        """ 
        
        if self.optim_type == 'complete':
            self.intercept = vector[0]
            self.phi = vector[1:self.p + 1]
            self.theta = vector[self.p + 1:]
        elif self.optim_type == 'no_intercept' or self.optim_type == 'optim_params':
            self.phi = vector[0:self.p]
            self.theta = vector[self.p:]
        elif self.optim_type == 'optim_intercept':
            self.intercept = vector[0]
        elif self.optim_type == 'no_optim':
            pass
            
        return self

    def __forward__(self, ts):
        
        lon_ts = len(ts.values)
            
        if self.p == 0:
            p_sum = 0
        elif lon_ts <= self.p:
            ts_last = ts.values[0:lon_ts]
            p_sum = self.intercept + numpy.dot(ts_last, self.phi[0:lon_ts])
        else:
            ts_last = ts.values[lon_ts-self.p:lon_ts]
            p_sum = self.intercept + numpy.dot(ts_last, self.phi)
        
        if self.q == 0:
            q_sum = 0
        else:
            history = list()
            predictions = list()
            for t in numpy.arange(0,lon_ts,1):
                length = len(history)
            
                if length <= self.q:
                    yhat = numpy.mean(ts.values[0:t])
                else:
                    ts_last = history[length-self.q:length]
                    predicted = predictions[length-self.q:length]
                    mean_predicted = numpy.mean(ts_last)
                    new_predicted = self.intercept + numpy.dot(numpy.subtract(ts_last, predicted), self.theta)
                    yhat = mean_predicted + new_predicted
            
                predictions.append(yhat)
                history.append(ts.values[t])
        
            if lon_ts == 1:
                q_sum = ts.values[0]
            elif lon_ts <= self.q:
                q_sum = numpy.mean(history[0:lon_ts])
            else:
                ts_last = history[lon_ts-self.q:lon_ts]
                predicted = predictions[lon_ts-self.q:lon_ts]
                mean_predicted = numpy.mean(ts_last)
                new_predicted = self.intercept + numpy.dot(numpy.subtract(ts_last, predicted), self.theta)
                q_sum = mean_predicted + new_predicted    
            
        result = p_sum + q_sum

        return result

    def predict(self, ts):
        """ Fits a time series using self model parameters
        
        Args:
            ts (pandas.Series): Time series to fit.
        
        Returns:
            Fitted time series.
            
        """

        prediction = list()
        for i in range(len(ts)):
            if i == 0:
                result = self.intercept
            else:
                result = self.__forward__(ts[0:i])
            prediction.append(result)
        prediction = pandas.Series((v for v in prediction), index = ts.index)
        return prediction


    def fit(self, ts, error_function = None):
        """ Finds optimal parameters using a given optimization function
        
        Args:
            ts (pandas.Series): Time series to fit.
            error_function (function): Function to estimates error.
            
        Return:
            self
        
        """
        
        if self.optim_type == 'no_optim':
            pass
        else:
            def f(x):
                self.vector2params(x)
                return self.calc_error(ts, error_function)

            x0 = self.params2vector()
            optim_params = scipy.optimize.minimize(f, x0)
            self.vector2params(vector = optim_params.x)

        return self

    def forecast(self, ts, periods, confidence_interval = None, iterations = 300):
        """ Predicts future values in a given period
        
        Args:
            ts (pandas.Series): Time series to predict.
            periods (int): Number of periods ahead to predict.
            
        Returns:
            Time series of predicted values.
        
        """
        for i in range(periods):
            if i == 0:
                y = ts

            value = self.__forward__(y)
            y = add_next_date(y, value)
        
        if confidence_interval == None:
            for i in range(periods):
                if i == 0:
                    ci_zero = ts
                ci_zero = add_next_date(ci_zero, None)
            
            ci_inf = ci_zero[-periods:]
            ci_sup = ci_zero[-periods:]
            ci = pandas.DataFrame([ci_inf, ci_sup], index = ['ci_inf', 'ci_sup'])            
        else:
            ci = self.simulate(ts, periods, confidence_interval, iterations)
            
        prediction = y[-periods:]
        prediction.name = 'series'
        result = ci.append(prediction)

        return result.transpose()