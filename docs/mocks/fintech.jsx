import React, { useState, useEffect, useCallback } from 'react';

// Define the custom model and API endpoint constants
const API_KEY = ""; // Canvas will automatically provide this in runtime
const SYSTEM_INSTRUCTION = "You are 'Nexus Analyst,' a friendly, helpful AI designed to translate complex financial data into simple, actionable insights. Your explanations must be clear, concise, use everyday analogies, and avoid jargon where possible. Always maintain a positive and professional tone. Your analysis must focus on the risk and reward of the specific options contract provided.";

// --- Mock Data Structures ---

const nexusColors = {
    blue: '#004AAD', // Deeper blue for improved contrast
    dark: '#1e293b',
    light: '#f1f5f9'
};

const INITIAL_MOCK_PORTFOLIO = {
    cash: 15200.50,
    totalValue: 55200.50,
    holdings: [
        { 
            ticker: 'AAPL', type: 'Stock', quantity: 150, purchasePrice: 189.50, currentPrice: 195.20, todayChange: 1.25, todayPct: 0.65, 
            totalGain: 855.00, totalPct: 3.05, expiry: null, position: 'Long', 
            details: { basis: 189.50, taxLot: 'LIFO', marketValue: 29280.00 } 
        },
        { 
            ticker: 'TSLA', type: 'Stock', quantity: 50, purchasePrice: 190.50, currentPrice: 180.10, todayChange: -2.00, todayPct: -1.10, 
            totalGain: -520.00, totalPct: -5.45, expiry: null, position: 'Long',
            details: { basis: 190.50, taxLot: 'FIFO', marketValue: 9005.00 } 
        },
        { 
            ticker: 'GOOGL', type: 'Call Option', quantity: 5, purchasePrice: 3.50, currentPrice: 4.10, todayChange: 0.25, todayPct: 6.50, 
            totalGain: 300.00, totalPct: 17.14, expiry: '2025-12-19', position: 'Long',
            details: { basis: 3.50, marketValue: 2050.00, multiplier: 100 } 
        },
        { 
            ticker: 'MSFT', type: 'Stock', quantity: -20, purchasePrice: 400.00, currentPrice: 420.00, todayChange: 5.00, todayPct: 1.20, 
            totalGain: 400.00, totalPct: 5.00, expiry: null, position: 'Short', // Short position example
            details: { basis: 400.00, taxLot: 'N/A', marketValue: -8400.00 } 
        },
    ]
};

const MOCK_HISTORY_DATA = [
    { date: 'Jan 2025', value: 45000 },
    { date: 'Feb 2025', value: 48500 },
    { date: 'Mar 2025', value: 51200 },
    { date: 'Apr 2025', value: 50500 },
    { date: 'May 2025', value: 52100 },
    { date: 'Jun 2025', value: 55200.50 }, 
];

// --- Comprehensive Mock Data for Stock Details (Includes Mock Verdict) ---
const MOCK_STOCK_DETAILS = {
    GOOGL: {
        overallMetrics: { price: 175.50, volumeStatus: 'Above Average', volatilityStatus: 'Moderate', valuationStatus: 'Slightly Undervalued' },
        verdict: { recommendation: 'Strong Buy', sentiment: 'Positive' },
        details: {
            Fundamental: [
                { name: 'Revenue Growth (YoY)', value: '15.2%', meaning: 'Strongly suggests the company is successfully selling more products or services.', sentiment: 'Positive' },
                { name: 'Net Profit Margin', value: '23.8%', meaning: 'Excellent: The company keeps a large portion of every dollar earned as pure profit.', sentiment: 'Positive' },
                { name: 'Debt-to-Equity (D/E) Ratio', value: '0.15', meaning: 'Very low debt. The company relies mostly on its own money, making it financially safe.', sentiment: 'Positive' },
                { name: 'P/E Ratio', value: '25.0x', meaning: 'A bit higher than average, suggesting investors expect good future growth.', sentiment: 'Neutral' },
                { name: 'Free Cash Flow (FCF)', value: '$18B', meaning: 'High FCF indicates lots of excess cash for dividends, buybacks, or R&D.', sentiment: 'Positive' },
            ],
            Technical: [
                { name: '50-Day Moving Average (SMA)', value: '170.00', meaning: 'The current price is above this average, indicating a short-term upward trend is developing.', sentiment: 'Positive' },
                { name: 'Relative Strength Index (RSI)', value: '75', meaning: 'The stock is technically "Overbought," meaning it might be due for a small pullback soon.', sentiment: 'Negative' },
                { name: 'MACD', value: 'Crossing Up', meaning: 'The shorter-term momentum is accelerating past the longer-term momentum—a bullish sign.', sentiment: 'Positive' },
                { name: 'Support Level', value: '165.00', meaning: 'Strong price floor. If the stock drops here, buyers are expected to step in and stop the fall.', sentiment: 'Positive' },
            ],
            Sentiment: [
                { name: 'VIX (Volatility Index)', value: '14.5', meaning: 'Low volatility, meaning the market is calm and investors are feeling confident (not fearful).', sentiment: 'Positive' },
                { name: 'Short Interest', value: '0.8%', meaning: 'Very few investors are betting against the stock, showing high market confidence.', sentiment: 'Positive' },
                { name: 'Put/Call Ratio', value: '0.95', meaning: 'Slightly more buyers are buying Put options (betting down) than Call options (betting up)—mild caution.', sentiment: 'Neutral' },
            ],
            Qualitative: [
                { name: 'Management Quality', value: 'Excellent', meaning: 'Experienced and visionary leaders, highly capable of navigating industry changes.', sentiment: 'Positive' },
                { name: 'Competitive Advantage (Moat)', value: 'Strong Network Effect', meaning: 'Its large user base makes it extremely hard for competitors to replace its services.', sentiment: 'Positive' },
                { name: 'Innovation & R&D', value: 'High', meaning: 'Heavy investment in future tech (AI/Cloud) ensures long-term revenue streams.', sentiment: 'Positive' },
            ],
            Performance: [
                { name: 'Beta (vs S&P 500)', value: '1.15', meaning: 'The stock moves 15% more aggressively than the overall market (S&P 500). Higher risk, higher potential reward.', sentiment: 'Neutral' },
                { name: 'Sharpe Ratio (1yr)', value: '1.25', meaning: 'Good return for the level of risk taken. Better than most similar investments.', sentiment: 'Positive' },
                { name: 'Drawdown (Last 12mo)', value: '-12%', meaning: 'The largest drop in value over the last year. Shows maximum pain during corrections.', sentiment: 'Negative' },
            ],
        }
    },
    DEFAULT: {
        overallMetrics: { price: 100.00, volumeStatus: 'Average', volatilityStatus: 'Average', valuationStatus: 'Neutral' },
        verdict: { recommendation: 'Hold', sentiment: 'Neutral' },
        details: {
            Fundamental: [{ name: 'P/E Ratio', value: '15x', meaning: 'Fairly priced compared to earnings.', sentiment: 'Neutral' }],
            Technical: [{ name: 'RSI', value: '50', meaning: 'No clear buy or sell signal.', sentiment: 'Neutral' }],
            Sentiment: [{ name: 'VIX', value: '20', meaning: 'Market is moderately uncertain.', sentiment: 'Neutral' }],
            Qualitative: [{ name: 'Management Quality', value: 'Average', meaning: 'Standard operational effectiveness.', sentiment: 'Neutral' }],
            Performance: [{ name: 'Beta', value: '1.0', meaning: 'Stock moves in line with the overall market.', sentiment: 'Neutral' }],
        }
    }
};

// --- Updated Mock Data for Options Chains (Includes Mock Verdict) ---
const MOCK_OPTIONS_CHAINS = {
    GOOGL: {
        currentPrice: 175.50,
        contracts: [
            // CALLS - Expiring Dec 2025
            { 
                id: "GOOGL251219C170", type: 'Call', strike: 170, expiry: '2025-12-19', premium: 7.50, dte: 60, delta: 0.78, gamma: 0.015, theta: -0.06, vega: 0.12,
                verdict: { recommendation: 'Buy to Open (Conservative)', sentiment: 'Positive' },
                details: {
                    'CoreParameters': [
                        { name: 'Underlying Price (S₀)', value: '$175.50', meaning: 'The stock price is currently above the strike price.', sentiment: 'Positive' },
                        { name: 'Strike Price (K)', value: '$170.00', meaning: 'This is an In-The-Money (ITM) option, already profitable.', sentiment: 'Positive' },
                        { name: 'Time to Expiration (T)', value: '60 Days', meaning: 'A short time window, increasing the impact of time decay (Theta).', sentiment: 'Neutral' },
                        { name: 'Implied Volatility (IV)', value: '30%', meaning: 'The market expects moderate future price swings.', sentiment: 'Neutral' },
                        { name: 'Historical Volatility (HV)', value: '25%', meaning: 'IV is currently higher than the stock\'s past movements, suggesting the premium is slightly high.', sentiment: 'Negative' }
                    ],
                    'ValueOutputs': [
                        { name: 'Option Premium', value: '$7.50', meaning: 'The total cost to purchase one contract (7.50 x 100).', sentiment: 'Neutral' },
                        { name: 'Intrinsic Value', value: '$5.50', meaning: 'A large portion of the price is real, current value.', sentiment: 'Positive' },
                        { name: 'Time Value', value: '$2.00', meaning: 'The remaining portion of the price is purely speculation on future movement.', sentiment: 'Neutral' },
                        { name: 'Breakeven Point', value: '$177.50', meaning: 'The stock must reach this price by expiration to recover your cost.', sentiment: 'Neutral' },
                    ],
                    'Greeks': [
                        { name: 'Delta (Δ)', value: '0.78', meaning: 'Moves almost dollar-for-dollar with the stock. Low leverage, high probability.', sentiment: 'Neutral' },
                        { name: 'Gamma (Γ)', value: '0.015', meaning: 'Delta\'s change (acceleration) is slow, making the option\'s movement predictable.', sentiment: 'Positive' },
                        { name: 'Theta (Θ)', value: '-0.06', meaning: 'Losing $6.00 per contract daily due to time decay.', sentiment: 'Negative' },
                        { name: 'Vega (ν)', value: '0.12', meaning: 'Highly sensitive to volatility changes: up 1% IV means $12 gain/contract.', sentiment: 'Positive' }
                    ],
                    'MarketTrading': [
                        { name: 'Moneyness', value: 'In-the-Money (ITM)', meaning: 'Low speculation, high probability of profit.', sentiment: 'Positive' },
                        { name: 'Open Interest', value: '5,000', meaning: 'Moderate open interest provides good liquidity.', sentiment: 'Neutral' },
                        { name: 'Put/Call Ratio (Total)', value: '0.85', meaning: 'Overall market sentiment is bullish (more calls being bought than puts).', sentiment: 'Positive' }
                    ],
                    'RiskPerformance': [
                        { name: 'Max Profit', value: 'Unlimited', meaning: 'Potential gains are uncapped if the stock moves up.', sentiment: 'Positive' },
                        { name: 'Max Loss', value: '$750.00', meaning: 'Your maximum risk is limited to the premium paid.', sentiment: 'Neutral' },
                        { name: 'Probability of Profit (POP)', value: '75%', meaning: 'High chance the option will expire in the money.', sentiment: 'Positive' }
                    ],
                }
            },
            { 
                id: "GOOGL251219C180", type: 'Call', strike: 180, expiry: '2025-12-19', premium: 4.10, dte: 60, delta: 0.55, gamma: 0.035, theta: -0.05, vega: 0.08,
                verdict: { recommendation: 'Avoid: High Gamma Risk', sentiment: 'Negative' },
                details: {
                    'CoreParameters': [
                        { name: 'Underlying Price (S₀)', value: '$175.50', meaning: 'The stock price is below the strike price.', sentiment: 'Negative' },
                        { name: 'Strike Price (K)', value: '$180.00', meaning: 'This is an Out-of-the-Money (OTM) option, requiring stock growth.', sentiment: 'Neutral' },
                        { name: 'Time to Expiration (T)', value: '60 Days', meaning: 'A short time window for the stock to reach the target price.', sentiment: 'Neutral' },
                        { name: 'Implied Volatility (IV)', value: '35%', meaning: 'The market expects higher future price swings.', sentiment: 'Neutral' },
                        { name: 'Historical Volatility (HV)', value: '25%', meaning: 'IV is much higher than past moves, suggesting the option might be overpriced.', sentiment: 'Negative' }
                    ],
                    'ValueOutputs': [
                        { name: 'Option Premium', value: '$4.10', meaning: 'The total cost to purchase one contract (4.10 x 100).', sentiment: 'Neutral' },
                        { name: 'Intrinsic Value', value: '$0.00', meaning: 'The entire price is time value, a high-risk bet.', sentiment: 'Negative' },
                        { name: 'Time Value', value: '$4.10', meaning: '100% of the price is for potential future movement.', sentiment: 'Negative' },
                        { name: 'Breakeven Point', value: '$184.10', meaning: 'The stock must gain significantly to recover your cost.', sentiment: 'Neutral' },
                    ],
                    'Greeks': [
                        { name: 'Delta (Δ)', value: '0.55', meaning: 'Gains $0.55 for every $1 stock move. Good leverage for direction.', sentiment: 'Positive' },
                        { name: 'Gamma (Γ)', value: '0.035', meaning: 'Delta\'s change (acceleration) is high, meaning profits/losses accelerate quickly.', sentiment: 'Negative' },
                        { name: 'Theta (Θ)', value: '-0.05', meaning: 'Losing $5.00 per contract daily due to time decay.', sentiment: 'Negative' },
                        { name: 'Vega (ν)', value: '0.08', meaning: 'Sensitive to volatility: up 1% IV means $8 gain/contract.', sentiment: 'Positive' }
                    ],
                    'MarketTrading': [
                        { name: 'Moneyness', value: 'Out-of-the-Money (OTM)', meaning: 'High speculation, low probability of profit.', sentiment: 'Negative' },
                        { name: 'Open Interest', value: '15,000', meaning: 'Very high open interest ensures excellent liquidity.', sentiment: 'Positive' },
                        { name: 'Put/Call Ratio (Total)', value: '0.85', meaning: 'Overall market sentiment is bullish.', sentiment: 'Positive' }
                    ],
                    'RiskPerformance': [
                        { name: 'Max Profit', value: 'Unlimited', meaning: 'Potential gains are uncapped.', sentiment: 'Positive' },
                        { name: 'Max Loss', value: '$410.00', meaning: 'Lower maximum risk than the ITM option.', sentiment: 'Positive' },
                        { name: 'Probability of Profit (POP)', value: '48%', meaning: 'Model predicts a near 50/50 chance of finishing profitable.', sentiment: 'Neutral' }
                    ],
                }
            },
            // PUTS - Expiring Dec 2025
            { 
                id: "GOOGL251219P170", type: 'Put', strike: 170, expiry: '2025-12-19', premium: 3.50, dte: 60, delta: -0.45, gamma: 0.030, theta: -0.04, vega: 0.07,
                verdict: { recommendation: 'Wait for Dip (Bearish)', sentiment: 'Neutral' },
                details: {
                    'CoreParameters': [
                        { name: 'Underlying Price (S₀)', value: '$175.50', meaning: 'The stock is currently trading above the put strike price.', sentiment: 'Negative' },
                        { name: 'Strike Price (K)', value: '$170.00', meaning: 'The stock must drop below this price for the put to become profitable.', sentiment: 'Neutral' },
                        { name: 'Time to Expiration (T)', value: '60 Days', meaning: 'You need a bearish move to happen soon.', sentiment: 'Neutral' },
                        { name: 'Implied Volatility (IV)', value: '33%', meaning: 'The market expects moderate to high future price swings.', sentiment: 'Neutral' },
                        { name: 'Historical Volatility (HV)', value: '25%', meaning: 'IV is higher than past moves, suggesting the put option might be overpriced.', sentiment: 'Negative' }
                    ],
                    'ValueOutputs': [
                        { name: 'Option Premium', value: '$3.50', meaning: 'The total cost to purchase one contract (3.50 x 100).', sentiment: 'Neutral' },
                        { name: 'Intrinsic Value', value: '$0.00', meaning: 'No current value; entire premium is time value.', sentiment: 'Negative' },
                        { name: 'Time Value', value: '$3.50', meaning: '100% of the price is for potential future movement.', sentiment: 'Negative' },
                        { name: 'Breakeven Point', value: '$166.50', meaning: 'The stock needs to fall to this level for you to recoup your premium.', sentiment: 'Neutral' },
                    ],
                    'Greeks': [
                        { name: 'Delta (Δ)', value: '-0.45', meaning: 'If stock drops $1, option gains $0.45. Good sensitivity to downside.', sentiment: 'Positive' },
                        { name: 'Gamma (Γ)', value: '0.030', meaning: 'High acceleration means the option\'s effectiveness changes rapidly.', sentiment: 'Negative' },
                        { name: 'Theta (Θ)', value: '-0.04', meaning: 'Losing $4.00 per contract daily due to time decay.', sentiment: 'Negative' },
                        { name: 'Vega (ν)', value: '0.07', meaning: 'Sensitive to volatility: up 1% IV means $7 gain/contract.', sentiment: 'Positive' }
                    ],
                    'MarketTrading': [
                        { name: 'Moneyness', value: 'Out-of-the-Money (OTM)', meaning: 'Speculative bet on the stock falling significantly.', sentiment: 'Negative' },
                        { name: 'Open Interest', value: '25,000', meaning: 'Extremely high interest suggests this is a popular hedge or bearish bet.', sentiment: 'Positive' },
                        { name: 'Put/Call Ratio (Total)', value: '0.85', meaning: 'Overall market sentiment is still bullish, posing a risk to a short-term put.', sentiment: 'Negative' }
                    ],
                    'RiskPerformance': [
                        { name: 'Max Profit', value: '$1,665.00', meaning: 'Maximum profit if the stock drops to zero (Strike - Premium).', sentiment: 'Positive' },
                        { name: 'Max Loss', value: '$350.00', meaning: 'Your risk is limited to the premium paid.', sentiment: 'Positive' },
                        { name: 'Probability of Profit (POP)', value: '45%', meaning: 'Model predicts a slightly lower chance of finishing profitable.', sentiment: 'Negative' }
                    ],
                }
            },
            // CALLS - Expiring Mar 2026
            { 
                id: "GOOGL260320C190", type: 'Call', strike: 190, expiry: '2026-03-20', premium: 5.80, dte: 140, delta: 0.40, gamma: 0.020, theta: -0.02, vega: 0.15,
                verdict: { recommendation: 'Strong Buy: Volatility Play', sentiment: 'Positive' },
                details: {
                    'CoreParameters': [
                        { name: 'Underlying Price (S₀)', value: '$175.50', meaning: 'The stock price is significantly below the strike price.', sentiment: 'Negative' },
                        { name: 'Strike Price (K)', value: '$190.00', meaning: 'This is a long-term Out-of-the-Money (OTM) option, requiring patient growth.', sentiment: 'Neutral' },
                        { name: 'Time to Expiration (T)', value: '140 Days', meaning: 'Longer time frame gives the stock more time to rally.', sentiment: 'Positive' },
                        { name: 'Implied Volatility (IV)', value: '28%', meaning: 'Volatility is low compared to other contracts, making this a good buying opportunity.', sentiment: 'Positive' },
                        { name: 'Historical Volatility (HV)', value: '25%', meaning: 'IV is only slightly higher than past moves, suggesting a fair premium.', sentiment: 'Positive' }
                    ],
                    'ValueOutputs': [
                        { name: 'Option Premium', value: '$5.80', meaning: 'The total cost to purchase one contract (5.80 x 100).', sentiment: 'Neutral' },
                        { name: 'Intrinsic Value', value: '$0.00', meaning: 'No current value; entire premium is time value.', sentiment: 'Negative' },
                        { name: 'Time Value', value: '$5.80', meaning: '100% of the price is for potential future movement.', sentiment: 'Negative' },
                        { name: 'Breakeven Point', value: '$195.80', meaning: 'The stock needs a significant rally to become profitable.', sentiment: 'Negative' },
                    ],
                    'Greeks': [
                        { name: 'Delta (Δ)', value: '0.40', meaning: 'Lower delta means less gain per $1 move, but higher leverage.', sentiment: 'Neutral' },
                        { name: 'Gamma (Γ)', value: '0.020', meaning: 'Moderate acceleration; stable movement as the stock price changes.', sentiment: 'Neutral' },
                        { name: 'Theta (Θ)', value: '-0.02', meaning: 'Time decay is very slow, which is ideal for a long-term position.', sentiment: 'Positive' },
                        { name: 'Vega (ν)', value: '0.15', meaning: 'Very high sensitivity: excellent gains if market volatility increases.', sentiment: 'Positive' }
                    ],
                    'MarketTrading': [
                        { name: 'Moneyness', value: 'Out-of-the-Money (OTM)', meaning: 'Long-shot, high-reward speculative bet.', sentiment: 'Negative' },
                        { name: 'Open Interest', value: '1,200', meaning: 'Low open interest suggests slightly lower liquidity.', sentiment: 'Neutral' },
                        { name: 'Put/Call Ratio (Total)', value: '0.85', meaning: 'Overall market sentiment is bullish.', sentiment: 'Positive' }
                    ],
                    'RiskPerformance': [
                        { name: 'Max Profit', value: 'Unlimited', meaning: 'Potential gains are uncapped.', sentiment: 'Positive' },
                        { name: 'Max Loss', value: '$580.00', meaning: 'Moderate maximum risk.', sentiment: 'Neutral' },
                        { name: 'Probability of Profit (POP)', value: '35%', meaning: 'Model predicts a lower chance of finishing profitable due to the high strike.', sentiment: 'Negative' }
                    ],
                }
            },
        ]
    },
    DEFAULT: {
        currentPrice: 100.00,
        contracts: []
    }
};

// --- Utility Components ---

const LoadingIndicator = () => (
    <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-nexus-blue dark:border-blue-300 mr-3"></div>
        <p className="text-gray-500 dark:text-gray-400 text-sm">Nexus Analyst is crunching the data...</p>
    </div>
);

// --- New/Updated Components for Portfolio Tab ---

const PortfolioCard = ({ holding, totalEquityValue }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    
    // Calculate values based on mock data
    const totalCurrentValue = holding.quantity * holding.currentPrice * (holding.type.includes('Option') ? 100 : 1);
    const portfolioPercentage = (totalCurrentValue / totalEquityValue) * 100;

    const gainColorClass = holding.totalGain >= 0 ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400';
    const gainPrefix = holding.totalGain >= 0 ? '+' : '';
    
    const todayColorClass = holding.todayChange >= 0 ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400';
    const todayPrefix = holding.todayChange >= 0 ? '+' : '';

    const positionType = holding.position === 'Short' ? 'bg-red-500/10 text-red-700 dark:bg-red-900/50 dark:text-red-300 font-medium' : 'bg-green-500/10 text-green-700 dark:bg-green-900/50 dark:text-green-300 font-medium';
    const quantityDisplay = holding.position === 'Short' ? `Short ${Math.abs(holding.quantity)}` : `${Math.abs(holding.quantity)}`;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 mb-2 overflow-hidden">
            {/* Main Row */}
            <div 
                className={`flex items-center p-3 border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition duration-150`}
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex-1 min-w-0 pr-4">
                    <p className="font-extrabold text-lg text-nexus-dark dark:text-white">
                        {holding.ticker}
                        <span className={`text-xs ml-2 py-0.5 px-2 rounded-full ${positionType}`}>
                            {holding.type === 'Stock' ? holding.position : holding.type}
                        </span>
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        {quantityDisplay} {holding.type.includes('Option') ? 'Contracts' : 'Shares'}
                    </p>
                </div>

                {/* Grid for Wider Screens */}
                <div className="grid grid-cols-5 flex-1 gap-2 text-center text-sm hidden sm:grid">
                    {/* Today's Gain */}
                    <div className="font-medium">
                        <p className={todayColorClass}>{todayPrefix}{holding.todayChange.toFixed(2)}</p>
                        <p className={`text-xs ${todayColorClass}`}>{todayPrefix}{holding.todayPct.toFixed(2)}%</p>
                    </div>

                    {/* Total Gain */}
                    <div className="font-bold">
                        <p className={gainColorClass}>{gainPrefix}{holding.totalGain.toFixed(2)}</p>
                        <p className={`text-xs ${gainColorClass}`}>{gainPrefix}{holding.totalPct.toFixed(2)}%</p>
                    </div>
                    
                    {/* Current Price */}
                    <p className="text-gray-800 dark:text-gray-200 font-semibold">${holding.currentPrice.toFixed(2)}</p>

                    {/* Expiry / N/A */}
                    <p className="text-gray-500 dark:text-gray-400 text-xs font-mono">{holding.expiry || 'N/A'}</p>

                    {/* Portfolio % */}
                    <p className="text-nexus-blue dark:text-blue-400 font-extrabold">{portfolioPercentage.toFixed(1)}%</p>
                </div>

                {/* Arrow Icon for Expansion */}
                <div className="w-6 flex-shrink-0 text-center">
                    <svg className={`w-4 h-4 text-gray-400 transform transition-transform duration-200 ${isExpanded ? 'rotate-180' : 'rotate-0'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
            </div>

            {/* Expanded Details Row */}
            {isExpanded && (
                <div className="bg-gray-50 dark:bg-gray-700 p-3 sm:p-4 border-t border-gray-200 dark:border-gray-600 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div className="font-medium">
                        <p className="text-gray-500 dark:text-gray-400">Market Value</p>
                        <p className="text-gray-800 dark:text-gray-200 font-bold">${totalCurrentValue.toFixed(2)}</p>
                    </div>
                    <div className="font-medium">
                        <p className="text-gray-500 dark:text-gray-400">Purchase Price</p>
                        <p className="text-gray-800 dark:text-gray-200 font-bold">${holding.purchasePrice.toFixed(2)}</p>
                    </div>
                    <div className="font-medium">
                        <p className="text-gray-500 dark:text-gray-400">Tax Basis</p>
                        <p className="text-gray-800 dark:text-gray-200 font-bold">{holding.details.taxLot || 'FIFO'}</p>
                    </div>
                    <div className="font-medium">
                        <p className="text-gray-500 dark:text-gray-400">Unit Price</p>
                        <p className="text-gray-800 dark:text-gray-200 font-bold">${holding.currentPrice.toFixed(2)}</p>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- Chart Components (Unchanged logic, updated styling for dark mode) ---
const AllocationPieChart = ({ holdings, totalEquityValue }) => {
    let cumulativePercent = 0;
    const data = holdings.map(h => {
        const value = h.quantity * h.currentPrice * (h.type.includes('Option') ? 100 : 1);
        const percentage = totalEquityValue > 0 ? (value / totalEquityValue) * 100 : 0;
        const startOffset = cumulativePercent;
        cumulativePercent += percentage;
        const color = '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
        return {
            ticker: h.ticker, value: value, percentage: percentage, color: color, startOffset: startOffset, dasharray: `${percentage} ${100 - percentage}`,
        };
    }).sort((a, b) => b.value - a.value);

    if (data.length === 0 || totalEquityValue === 0) {
        return <div className="text-center p-8 text-gray-400 border border-dashed rounded-lg dark:border-gray-600">No holdings to display in chart.</div>;
    }

    return (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm flex flex-col items-center sm:flex-row sm:items-start">
            <div className="flex-shrink-0 mb-4 sm:mb-0" style={{ width: '150px', height: '150px' }}>
                <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                    <circle 
                        className="text-gray-200 dark:text-gray-700 stroke-current" 
                        strokeWidth="3.5" 
                        cx="18" cy="18" r="15.9155" 
                        fill="transparent" 
                        strokeDasharray="100 0" 
                    />
                    {data.map((item, index) => (
                        <circle
                            key={index}
                            stroke={item.color}
                            strokeWidth="3.5"
                            cx="18" cy="18" r="15.9155"
                            fill="transparent"
                            strokeDasharray={item.dasharray}
                            strokeDashoffset={100 - item.startOffset}
                            className="transition-all duration-700 ease-out"
                        >
                            <title>{item.ticker}: ${item.value.toFixed(2)} ({item.percentage.toFixed(1)}%)</title>
                        </circle>
                    ))}
                </svg>
            </div>
            
            <div className="sm:ml-6 flex-grow">
                <h3 className="text-lg font-semibold mb-3 text-nexus-dark dark:text-white">Allocation Breakdown</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                    {data.map((item, index) => (
                        <div key={index} className="flex items-center truncate">
                            <span style={{ backgroundColor: item.color }} className="w-3 h-3 rounded-full inline-block mr-2 flex-shrink-0"></span>
                            <span className="font-medium text-gray-700 dark:text-gray-300 truncate">{item.ticker}:</span>
                            <span className="ml-1 text-gray-600 dark:text-gray-300 font-bold flex-shrink-0"> {item.percentage.toFixed(1)}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const PortfolioHistoryChart = ({ historyData }) => {
    const width = 300;
    const height = 120;
    const padding = 10;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    if (!historyData || historyData.length < 2) {
        return <div className="text-center p-8 text-gray-400">Not enough history data to draw chart.</div>;
    }

    const values = historyData.map(d => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue;
    const numPoints = historyData.length;

    const scaleX = (index) => padding + (index / (numPoints - 1)) * chartWidth;
    const scaleY = (value) => {
        const normalized = (value - minValue) / range;
        return height - padding - normalized * chartHeight;
    };

    const linePath = historyData.map((d, i) => {
        const x = scaleX(i);
        const y = scaleY(d.value);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    return (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm mt-6">
            <h3 className="text-lg font-semibold mb-3 text-nexus-dark dark:text-white">6-Month Portfolio Value</h3>
            <div className="relative" style={{ width: '100%' }}>
                <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-auto">
                    <line x1={padding} y1={scaleY(maxValue)} x2={width - padding} y2={scaleY(maxValue)} stroke="#4b5563" strokeDasharray="2 2" />
                    <line x1={padding} y1={scaleY(minValue)} x2={width - padding} y2={scaleY(minValue)} stroke="#4b5563" strokeDasharray="2 2" />
                    <text x={padding - 5} y={scaleY(maxValue)} fontSize="6" fill="#9ca3af" textAnchor="end">${Math.round(maxValue)}</text>
                    <text x={padding - 5} y={scaleY(minValue) + 4} fontSize="6" fill="#9ca3af" textAnchor="end">${Math.round(minValue)}</text>

                    <path 
                        d={linePath} 
                        fill="none" 
                        stroke={nexusColors.blue} 
                        strokeWidth="1.5"
                    />

                    {historyData.map((d, i) => (
                        <circle
                            key={i}
                            cx={scaleX(i)}
                            cy={scaleY(d.value)}
                            r="2"
                            fill={nexusColors.blue}
                        >
                            <title>{d.date}: ${d.value.toFixed(2)}</title>
                        </circle>
                    ))}
                </svg>
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 pt-1 px-4">
                    {historyData.map((d, i) => (
                        <span key={i} className="flex-1 text-center">{d.date.split(' ')[0]}</span>
                    ))}
                </div>
            </div>
        </div>
    );
}

// --- LLM API Call Handlers (Unchanged) ---

const callGeminiApi = async (userQuery, tools = []) => {
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${API_KEY}`;
    
    const payload = {
        contents: [{ parts: [{ text: userQuery }] }],
        systemInstruction: { parts: [{ text: SYSTEM_INSTRUCTION }] },
        tools: tools.length > 0 ? [{ google_search: {} }] : undefined,
    };
    
    let lastError = null;
    for (let attempt = 0; attempt < 3; attempt++) {
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorBody = await response.text();
                throw new Error(`API call failed with status ${response.status}: ${errorBody}`);
            }

            const result = await response.json();
            const text = result.candidates?.[0]?.content?.parts?.[0]?.text || "Analysis failed to generate text.";
            return text;

        } catch (error) {
            lastError = error;
            console.error(`Attempt ${attempt + 1} failed:`, error.message);
            if (attempt < 2) {
                const delay = Math.pow(2, attempt) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    return `Error: Could not complete analysis after multiple attempts. Reason: ${lastError?.message || "Unknown error"}`;
};

// --- Analysis Sub-Components ---

const determineColor = (sentiment) => {
    if (sentiment === 'Positive') return 'text-green-500 dark:text-green-400';
    if (sentiment === 'Negative') return 'text-red-500 dark:text-red-400';
    return 'text-yellow-600 dark:text-yellow-400'; // Neutral or Caution
};

// New component for the verdict badge
const VerdictBadge = ({ recommendation, sentiment }) => {
    let bgColor, textColor, borderColor;

    switch (sentiment) {
        case 'Positive':
            bgColor = 'bg-green-100 dark:bg-green-900/50';
            textColor = 'text-green-700 dark:text-green-300';
            borderColor = 'border-green-500';
            break;
        case 'Negative':
            bgColor = 'bg-red-100 dark:bg-red-900/50';
            textColor = 'text-red-700 dark:text-red-300';
            borderColor = 'border-red-500';
            break;
        case 'Neutral':
        default:
            bgColor = 'bg-gray-100 dark:bg-gray-700';
            textColor = 'text-gray-700 dark:text-gray-300';
            borderColor = 'border-gray-500';
            break;
    }

    return (
        <div className={`p-3 rounded-lg border-l-4 shadow-sm ${bgColor} ${borderColor}`}>
            <p className="text-sm font-semibold mb-1 uppercase tracking-wider">Verdict:</p>
            <p className={`text-xl font-extrabold ${textColor}`}>{recommendation}</p>
        </div>
    );
};


const ParameterSection = ({ title, parameters }) => (
    <div className="space-y-4 p-4">
        <h3 className="text-xl font-bold mb-3 text-nexus-dark dark:text-white border-b dark:border-gray-700 pb-2">{title} Analysis</h3>
        {parameters.map((p, index) => (
            <div key={index} className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg border border-gray-200 dark:border-gray-600 shadow-sm">
                <div className="flex justify-between items-start">
                    <p className="font-bold text-gray-800 dark:text-gray-200">{p.name}</p>
                    <span className="font-semibold text-lg text-gray-900 dark:text-white">{p.value}</span>
                </div>
                <div className="mt-1 text-sm">
                    <span className={`font-extrabold mr-2 ${determineColor(p.sentiment)}`}>{p.sentiment}:</span>
                    <span className="text-gray-600 dark:text-gray-400 italic">{p.meaning}</span>
                </div>
            </div>
        ))}
    </div>
);


// --- Tab Content Components ---

const StockAnalysisTab = ({ stockTicker, setStockTicker, stockAnalysis, stockLoading, handleStockAnalysis }) => {
    
    const stockDetails = App.fetchStockDetails(stockTicker.toUpperCase());
    const overallMetrics = stockDetails.overallMetrics;
    const detailData = stockDetails.details;
    const verdict = stockDetails.verdict;

    const subTabs = [
        { id: 'Fundamental', label: 'Fundamental' },
        { id: 'Technical', label: 'Technical' },
        { id: 'Sentiment', label: 'Sentiment' },
        { id: 'Qualitative', label: 'Qualitative' },
        { id: 'Performance', label: 'Performance' },
    ];
    
    const [activeSubTab, setActiveSubTab] = useState('Fundamental');

    const renderSubContent = () => {
        const parameters = detailData[activeSubTab] || [];
        const label = subTabs.find(t => t.id === activeSubTab)?.label || 'Details';
        return <ParameterSection title={label} parameters={parameters} />;
    };

    return (
        <section className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-lg border-t-4 border-gray-300 dark:border-gray-700">
            <h2 className="text-2xl font-semibold mb-4" style={{ color: nexusColors.dark }}><span className="dark:text-white">
                Stock Market Analysis
            </span></h2>
            
            {/* Input and Analyze Button */}
            <div className="flex flex-col sm:flex-row gap-3 mb-6">
                <input
                    type="text"
                    className="flex-grow p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-nexus-blue focus:border-nexus-blue transition duration-150"
                    placeholder="Enter Stock Ticker (e.g., AAPL)"
                    value={stockTicker}
                    onChange={(e) => setStockTicker(e.target.value.toUpperCase())}
                    onKeyDown={(e) => e.key === 'Enter' && handleStockAnalysis()}
                />
                <button
                    onClick={handleStockAnalysis}
                    disabled={stockLoading || !stockTicker}
                    className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-lg shadow-xl hover:bg-indigo-700 transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {stockLoading ? 'Analyzing...' : `Analyze ${stockTicker || 'Stock'}`}
                </button>
            </div>
            
            {/* Overall Nexus Analyst Report (Summary) */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-6 shadow-inner border dark:border-gray-700">
                <h3 className="text-lg font-bold mb-2" style={{ color: nexusColors.blue }}>
                    Nexus Analyst Overall Report:
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 items-center">
                    <div className="col-span-1 md:col-span-3">
                        <p className="text-sm text-gray-700 dark:text-gray-300 font-semibold mb-3">
                            Price: <span className="font-bold">${overallMetrics.price}</span> | 
                            Volume: <span className="font-bold">{overallMetrics.volumeStatus}</span> | 
                            Volatility: <span className="font-bold">{overallMetrics.volatilityStatus}</span> | 
                            Valuation: <span className="font-bold">{overallMetrics.valuationStatus}</span>
                        </p>
                        {stockLoading ? <LoadingIndicator /> : (
                            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{stockAnalysis}</p>
                        )}
                    </div>
                    {/* Verdict Badge */}
                    <div className="col-span-1">
                        <VerdictBadge recommendation={verdict.recommendation} sentiment={verdict.sentiment} />
                    </div>
                </div>
            </div>

            {/* Sub-Tab Navigation (Styled as Underline) */}
            <div className="overflow-hidden border-b border-gray-300 dark:border-gray-700">
                <div className="flex flex-wrap sm:flex-nowrap">
                    {subTabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveSubTab(tab.id)}
                            className={`
                                py-2 px-4 text-xs sm:text-sm font-semibold transition duration-200 border-b-2
                                ${activeSubTab === tab.id
                                    ? 'border-nexus-blue text-nexus-blue dark:text-blue-400 dark:border-blue-400'
                                    : 'text-gray-600 border-transparent hover:border-gray-400 dark:text-gray-400 dark:hover:border-gray-500'
                                }
                            `}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Detailed Sub-Content */}
            <div className="bg-white dark:bg-gray-900 rounded-b-lg p-0">
                {renderSubContent()}
            </div>

        </section>
    );
}

const OptionsAnalysisTab = ({ optionsTicker, setOptionsTicker, optionsAnalysis, optionsLoading, handleOptionsAnalysis }) => {
    
    // NEW STATE: To store the entire chain and the selected contract details
    const [optionsChain, setOptionsChain] = useState([]);
    const [selectedContract, setSelectedContract] = useState(null);
    const [activeSubTab, setActiveSubTab] = useState('Greeks'); 

    // Function to set the selected contract and trigger analysis
    const handleContractSelection = useCallback((contract) => {
        setSelectedContract(contract);
        // Automatically trigger the analysis for the selected contract
        handleOptionsAnalysis(contract);
    }, [handleOptionsAnalysis]);

    // Handle contract details change from the main App component
    useEffect(() => {
        // Fetch and process the mock data when the ticker changes or on initial load
        const chainData = App.fetchOptionsChain(optionsTicker.toUpperCase());
        setOptionsChain(chainData.contracts);

        // If a contract was previously selected (for the new ticker), select the first contract by default
        if (chainData.contracts.length > 0 && !selectedContract) {
            handleContractSelection(chainData.contracts[0]);
        } else if (chainData.contracts.length > 0 && selectedContract && selectedContract.ticker !== optionsTicker.toUpperCase()) {
             // If we searched for a new ticker, reset the selected contract to the first one in the new chain
             handleContractSelection(chainData.contracts[0]);
        }
        
    }, [optionsTicker]); // Only re-run when the main ticker changes

    // Sub-tab logic
    const subTabs = [
        { id: 'CoreParameters', label: 'Core Parameters' },
        { id: 'ValueOutputs', label: 'Value Outputs' },
        { id: 'Greeks', label: 'Greeks' },
        { id: 'MarketTrading', label: 'Market/Trading' },
        { id: 'RiskPerformance', label: 'Risk/Performance' },
    ];
    
    const renderSubContent = () => {
        if (!selectedContract) return null;

        // Ensure we get the correct details for the currently selected contract
        const parameters = selectedContract.details[activeSubTab] || [];
        const label = subTabs.find(t => t.id === activeSubTab)?.label || 'Details';
        return <ParameterSection title={label} parameters={parameters} />;
    };

    const currentPrice = App.fetchOptionsChain(optionsTicker).currentPrice;


    return (
        <section className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-lg border-t-4 border-gray-300 dark:border-gray-700">
            <h2 className="text-2xl font-semibold mb-4" style={{ color: nexusColors.dark }}><span className="dark:text-white">
                Options Analysis
            </span></h2>
            
            {/* Input and Analyze Button (Now just for Ticker search) */}
            <div className="flex flex-col sm:flex-row gap-3 mb-6">
                <input
                    type="text"
                    className="flex-grow p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-nexus-blue focus:border-nexus-blue transition duration-150"
                    placeholder="Enter Stock Ticker (e.g., AAPL)"
                    value={optionsTicker}
                    onChange={(e) => setOptionsTicker(e.target.value.toUpperCase())}
                    onKeyDown={(e) => e.key === 'Enter' && setOptionsChain([])} // Clear chain on new ticker search
                />
                <button
                    onClick={() => {
                        setOptionsChain([]); // Forces the useEffect to run and fetch new chain data
                        setSelectedContract(null); // Clear selected contract
                    }}
                    disabled={optionsLoading || !optionsTicker}
                    className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-lg shadow-xl hover:bg-indigo-700 transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {optionsLoading ? 'Loading...' : `Load Chain for ${optionsTicker || 'Options'}`}
                </button>
            </div>

            {/* --- Options Chain Display --- */}
            {optionsChain.length > 0 && (
                <div className="mb-6">
                    <h3 className="text-xl font-bold mb-3 text-nexus-dark dark:text-white">
                        Options Chain for {optionsTicker} (Stock Price: <span className="text-green-500">${currentPrice.toFixed(2)}</span>)
                    </h3>
                    <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
                                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Strike</th>
                                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Expiry</th>
                                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Premium</th>
                                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">DTE</th>
                                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Delta</th>
                                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Theta</th>
                                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Vega</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {optionsChain.map((contract) => (
                                    <tr 
                                        key={contract.id}
                                        onClick={() => handleContractSelection(contract)}
                                        className={`cursor-pointer transition duration-150 
                                            ${selectedContract?.id === contract.id 
                                                ? 'bg-indigo-100 dark:bg-indigo-900/50 border-l-4 border-nexus-blue' 
                                                : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                                            }`
                                        }
                                    >
                                        <td className="px-3 py-2 whitespace-nowrap text-sm font-medium" style={{ color: contract.type === 'Call' ? 'green' : 'red' }}>
                                            {contract.type}
                                        </td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">${contract.strike.toFixed(2)}</td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">{contract.expiry}</td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">${contract.premium.toFixed(2)}</td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-center text-gray-600 dark:text-gray-400">{contract.dte}</td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-center text-gray-900 dark:text-gray-200">{contract.delta.toFixed(2)}</td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-center text-gray-900 dark:text-gray-200">{contract.theta.toFixed(2)}</td>
                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-center text-gray-900 dark:text-gray-200">{contract.vega.toFixed(2)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
            
            {/* --- Analysis Section (Visible ONLY after selection) --- */}
            {selectedContract ? (
                <>
                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-6 shadow-inner border dark:border-gray-700">
                        <h3 className="text-lg font-bold mb-2" style={{ color: nexusColors.blue }}>
                            Nexus Analyst Report for: <span className="text-indigo-600 dark:text-indigo-400">{selectedContract.type} ${selectedContract.strike.toFixed(2)} ({selectedContract.expiry})</span>
                        </h3>
                         <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 items-center">
                            <div className="col-span-1 md:col-span-3">
                                {optionsLoading ? <LoadingIndicator /> : (
                                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{optionsAnalysis}</p>
                                )}
                            </div>
                            {/* Verdict Badge */}
                            <div className="col-span-1">
                                <VerdictBadge 
                                    recommendation={selectedContract.verdict.recommendation} 
                                    sentiment={selectedContract.verdict.sentiment} 
                                />
                            </div>
                        </div>
                    </div>

                    {/* Sub-Tab Navigation (Styled as Underline) */}
                    <div className="overflow-hidden border-b border-gray-300 dark:border-gray-700">
                        <div className="flex flex-wrap sm:flex-nowrap">
                            {subTabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveSubTab(tab.id)}
                                    className={`
                                        py-2 px-4 text-xs sm:text-sm font-semibold transition duration-200 border-b-2
                                        ${activeSubTab === tab.id
                                            ? 'border-nexus-blue text-nexus-blue dark:text-blue-400 dark:border-blue-400'
                                            : 'text-gray-600 border-transparent hover:border-gray-400 dark:text-gray-400 dark:hover:border-gray-500'
                                        }
                                    `}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Detailed Sub-Content */}
                    <div className="bg-white dark:bg-gray-900 rounded-b-lg p-0">
                        {renderSubContent()}
                    </div>
                </>
            ) : (
                <div className="text-center p-12 bg-gray-50 dark:bg-gray-800 border border-dashed rounded-lg text-gray-500 dark:text-gray-400">
                    {optionsTicker.length > 0 ? (
                        'Select a contract from the options chain above to view detailed analysis.'
                    ) : (
                        'Enter a stock ticker (e.g., GOOGL) to load the options chain.'
                    )}
                </div>
            )}
        </section>
    );
}

const RecommendationTab = () => (
    <div className="p-6 bg-white dark:bg-gray-900 rounded-xl shadow-lg border-t-4 border-nexus-blue dark:border-blue-400">
        <h3 className="text-2xl font-semibold mb-4 text-nexus-dark dark:text-white">
            Personalized Investment Recommendations
        </h3>
        <div className="bg-blue-50 dark:bg-blue-900/30 p-6 rounded-lg border border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-3">Welcome to your Recommendation Dashboard.</p>
            <p className="text-sm">
                This area will feature AI-driven suggestions based on your portfolio (asset mix, risk tolerance) and market analysis from the other tabs. You could see **buy alerts for undervalued stocks**, **sell recommendations for overbought options**, or sector allocation adjustments here!
            </p>
            <ul className="list-disc list-inside mt-4 text-sm space-y-1">
                <li>**Actionable Alerts:** e.g., "GOOGL is Oversold, Consider Buy Signal."</li>
                <li>**Strategy Alignment:** e.g., "Reduce High-Gamma Exposure Before Earnings."</li>
            </ul>
        </div>
    </div>
);

const NewsTab = () => {
    // Mock news data
    const mockNews = [
        { id: 1, headline: "S&P 500 futures rise as inflation concerns ease.", source: "Reuters", time: "10 mins ago", sentiment: "Positive", color: "text-green-600 dark:text-green-400" },
        { id: 2, headline: "Tech giant GOOGL announces record Q3 cloud revenue.", source: "Bloomberg", time: "25 mins ago", sentiment: "Positive", color: "text-green-600 dark:text-green-400" },
        { id: 3, headline: "Fed Chair signals potential rate hike delays due to job data.", source: "Wall Street Journal", time: "1 hour ago", sentiment: "Neutral", color: "text-gray-600 dark:text-gray-400" },
        { id: 4, headline: "TSLA stock drops on delivery miss forecast for next quarter.", source: "MarketWatch", time: "2 hours ago", sentiment: "Negative", color: "text-red-600 dark:text-red-400" },
        { id: 5, headline: "MSFT wins major government AI infrastructure contract.", source: "Yahoo Finance", time: "3 hours ago", sentiment: "Positive", color: "text-green-600 dark:text-green-400" },
    ];

    return (
        <div className="p-6 bg-white dark:bg-gray-900 rounded-xl shadow-lg border-t-4 border-nexus-blue dark:border-blue-400">
            <h3 className="text-2xl font-semibold mb-6 text-nexus-dark dark:text-white">
                Market and Stock Headlines
            </h3>
            <div className="space-y-4">
                {mockNews.map(news => (
                    <div key={news.id} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition duration-150">
                        <div className="flex justify-between items-start">
                            <p className="font-semibold text-gray-900 dark:text-gray-200 pr-4">{news.headline}</p>
                            <span className={`text-xs font-bold whitespace-nowrap ${news.color}`}>{news.sentiment.toUpperCase()}</span>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {news.source} 
                            <span className="ml-3 italic">({news.time})</span>
                        </p>
                    </div>
                ))}
            </div>
            <div className="mt-6 text-center">
                <button className="text-nexus-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm">
                    View Full News Feed &rarr;
                </button>
            </div>
        </div>
    );
};


const PortfolioTab = ({ portfolio, addHolding, historyData }) => {
    const [showAddForm, setShowAddForm] = useState(false);
    const [newHolding, setNewHolding] = useState({ ticker: '', quantity: '', currentPrice: '', type: 'Stock', position: 'Long' }); 

    // Recalculate total equity value (must account for option multiplier and short positions)
    const calculateTotalEquityValue = (holdings) => {
        return holdings.reduce((sum, h) => {
            const multiplier = h.type.includes('Option') ? 100 : 1;
            // Short positions reduce net value, so we use the actual quantity (which is negative)
            return sum + (h.quantity * h.currentPrice * multiplier);
        }, 0);
    };

    const totalEquityValue = calculateTotalEquityValue(portfolio.holdings);
    const totalAccountValue = portfolio.cash + totalEquityValue;


    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setNewHolding(prev => ({ 
            ...prev, 
            [name]: value,
            // Auto-set position if type changes
            ...(name === 'type' && !value.includes('Option') ? { position: 'Long' } : {}) 
        }));
    };

    const handleAdd = (e) => {
        e.preventDefault();
        let { ticker, quantity, currentPrice, type, position } = newHolding;

        if (!ticker || !quantity || !currentPrice || !type) {
            console.error("Please fill all required fields for the new holding.");
            return;
        }

        let parsedQuantity = parseFloat(quantity);
        // If the position is Short, the quantity must be stored as negative for calculations
        if (position === 'Short') {
             parsedQuantity = -Math.abs(parsedQuantity);
        } else {
             parsedQuantity = Math.abs(parsedQuantity);
        }

        const newAsset = {
            ticker: ticker.toUpperCase(),
            type: type,
            quantity: parsedQuantity,
            purchasePrice: parseFloat(currentPrice),
            currentPrice: parseFloat(currentPrice) * 1.01, // Mock small initial gain for visual effect
            todayChange: 0.00, 
            todayPct: 0.00,
            totalGain: (parsedQuantity * (parseFloat(currentPrice) * 1.01)) - (parsedQuantity * parseFloat(currentPrice)),
            totalPct: 1.00,
            expiry: type.includes('Option') ? '2026-06-18' : null, 
            position: parsedQuantity < 0 ? 'Short' : 'Long',
            details: { basis: parseFloat(currentPrice), taxLot: 'FIFO', marketValue: parsedQuantity * (parseFloat(currentPrice) * 1.01) * (type.includes('Option') ? 100 : 1), multiplier: type.includes('Option') ? 100 : 1 }
        };

        addHolding(newAsset);
        setNewHolding({ ticker: '', quantity: '', currentPrice: '', type: 'Stock', position: 'Long' }); 
        setShowAddForm(false);
    };

    return (
        <section className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-lg border-t-4 border-green-500 dark:border-green-700">
            <h2 className="text-2xl font-semibold mb-4 text-nexus-dark dark:text-white">
                Current Portfolio Summary
            </h2>
            
            {/* Value Summary */}
            <div className="mb-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg dark:bg-gray-800">
                <div className="flex justify-between items-end mb-2">
                    <span className="text-xl font-medium text-gray-500 dark:text-gray-400">Total Account Value:</span>
                    <span className="text-3xl font-extrabold text-green-600 dark:text-green-400">${totalAccountValue.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-base">
                    <span className="text-gray-500 dark:text-gray-400">Available Cash:</span>
                    <span className="text-gray-900 dark:text-gray-200 font-medium">${portfolio.cash.toFixed(2)}</span>
                </div>
            </div>

            {/* Charts: Line Chart for History and Pie Chart for Allocation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <PortfolioHistoryChart historyData={MOCK_HISTORY_DATA} />
                <AllocationPieChart holdings={portfolio.holdings} totalEquityValue={totalEquityValue} />
            </div>

            {/* ADD NEW STOCK OR OPTION BUTTON */}
            <div className="mt-6 mb-8">
                <button
                    onClick={() => setShowAddForm(true)}
                    className="w-full py-3 text-lg bg-green-600 text-white font-bold rounded-lg shadow-xl hover:bg-green-700 transition duration-150 flex items-center justify-center"
                >
                    <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                    ADD NEW STOCK OR OPTION
                </button>
            </div>


            <h3 className="text-lg font-semibold mb-3 border-b dark:border-gray-700 pb-2 text-nexus-dark dark:text-white">Holdings ({portfolio.holdings.length})</h3>

            {/* Holdings Table Header (Only visible on medium/larger screens) */}
            <div className="hidden sm:flex bg-gray-100 dark:bg-gray-700 p-3 rounded-t-lg text-xs font-semibold uppercase text-gray-600 dark:text-gray-300">
                <div className="flex-1 min-w-0 pr-4">Asset / Type</div>
                <div className="grid grid-cols-5 flex-1 gap-2 text-center">
                    <div>Today's Gain</div>
                    <div>Total Gain</div>
                    <div>Current Price</div>
                    <div>Expiry</div>
                    <div>Portfolio %</div>
                </div>
                <div className="w-6 flex-shrink-0"></div> {/* Spacer for icon */}
            </div>

            {/* Holding List */}
            <div className="space-y-2">
                {portfolio.holdings.map((h, index) => (
                    <PortfolioCard key={index} holding={h} totalEquityValue={totalEquityValue} />
                ))}
            </div>
            
            {/* Add Holding Form/Modal (Conditional Rendering) */}
            {showAddForm && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-2xl w-full max-w-md">
                        <h3 className="text-xl font-bold mb-4 text-nexus-dark dark:text-white">Add New Asset</h3>
                        <form onSubmit={handleAdd} className="space-y-4">
                            
                            {/* Asset Type Selector */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Asset Type</label>
                                <select
                                    name="type"
                                    value={newHolding.type}
                                    onChange={handleFormChange}
                                    className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-nexus-blue focus:border-nexus-blue"
                                    required
                                >
                                    <option value="Stock">Stock</option>
                                    <option value="Call Option">Call Option</option>
                                    <option value="Put Option">Put Option</option>
                                </select>
                            </div>
                            
                            {/* Position Type Selector (Only for Stocks - ENHANCED VISIBILITY) */}
                            {newHolding.type === 'Stock' && (
                                <div>
                                    <label className="block text-base font-bold text-gray-700 dark:text-gray-300 mb-1">
                                        Position Type
                                    </label>
                                    <select
                                        name="position"
                                        value={newHolding.position}
                                        onChange={handleFormChange}
                                        className="w-full p-3 border-2 border-indigo-300 dark:border-indigo-700 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 dark:text-white font-semibold focus:ring-nexus-blue focus:border-nexus-blue"
                                        required
                                    >
                                        <option value="Long">Long (Expect Price UP)</option>
                                        <option value="Short">Short (Expect Price DOWN)</option>
                                    </select>
                                </div>
                            )}

                            <input
                                type="text"
                                name="ticker"
                                placeholder="Stock Ticker (e.g., VOO)"
                                value={newHolding.ticker}
                                onChange={handleFormChange}
                                className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-nexus-blue focus:border-nexus-blue"
                                maxLength="5"
                                required
                            />
                            
                            <input
                                type="number"
                                name="quantity"
                                placeholder={newHolding.type.includes('Option') ? "Contracts (e.g., 5)" : "Shares (e.g., 10)"}
                                value={newHolding.quantity}
                                onChange={handleFormChange}
                                className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-nexus-blue focus:border-nexus-blue"
                                min="1"
                                step="any"
                                required
                            />
                            
                            <input
                                type="number"
                                name="currentPrice"
                                placeholder={newHolding.type.includes('Option') ? "Premium Paid (e.g., 3.50)" : "Purchase Price (e.g., 250.00)"}
                                value={newHolding.currentPrice}
                                onChange={handleFormChange}
                                className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-nexus-blue focus:border-nexus-blue"
                                min="0.01"
                                step="0.01"
                                required
                            />
                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowAddForm(false);
                                        setNewHolding({ ticker: '', quantity: '', currentPrice: '', type: 'Stock', position: 'Long' }); // Reset on cancel
                                    }}
                                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition duration-150"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-green-500 text-white font-medium rounded-lg hover:bg-green-600 transition duration-150"
                                >
                                    Save Holding
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </section>
    );
};

// --- NEW HomeTab Component ---

const HomeTab = ({ portfolio, addHolding, historyData }) => {
    // Set Recommendation as default sub-tab
    const [activeSubTab, setActiveSubTab] = useState('Recommendation');
    
    const subTabs = [
        { id: 'Recommendation', label: 'Recommendations' },
        { id: 'Portfolio', label: 'Portfolio' },
        { id: 'News', label: 'Market News' }, // Added new sub-tab
    ];

    const renderSubContent = () => {
        switch (activeSubTab) {
            case 'Portfolio':
                return <PortfolioTab portfolio={portfolio} addHolding={addHolding} historyData={historyData} />;
            case 'Recommendation':
                return <RecommendationTab />;
            case 'News': // Render News Tab
                return <NewsTab />;
            default:
                return null;
        }
    };

    return (
        <section className="mt-0">
            {/* Sub-Tab Navigation (Styled as Underline) */}
            <div className="overflow-hidden border-b border-gray-300 dark:border-gray-700">
                <div className="flex flex-wrap sm:flex-nowrap">
                    {subTabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveSubTab(tab.id)}
                            className={`
                                py-2 px-4 text-xs sm:text-sm font-semibold transition duration-200 border-b-2
                                ${activeSubTab === tab.id
                                    ? 'border-nexus-blue text-nexus-blue dark:text-blue-400 dark:border-blue-400'
                                    : 'text-gray-600 border-transparent hover:border-gray-400 dark:text-gray-400 dark:hover:border-gray-500'
                                }
                            `}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Sub-Content Area */}
            <div className="mt-4">
                {renderSubContent()}
            </div>
        </section>
    );
};


// --- Main Application Component ---

const App = () => {
    // Theme state
    const [theme, setTheme] = useState('light'); // 'light' or 'dark'

    // Set theme class on body (or relevant container)
    useEffect(() => {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.classList.add('dark');
        } else {
            root.classList.remove('dark');
        }
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
    };

    // Define color mappings for main tabs
    const tabColorClasses = {
        Home: { text: 'text-nexus-blue dark:text-blue-400', border: 'border-nexus-blue dark:border-blue-700', bg: 'bg-blue-50 dark:bg-blue-900/30' },
        StockAnalysis: { text: 'text-indigo-600 dark:text-indigo-400', border: 'border-indigo-600 dark:border-indigo-700', bg: 'bg-indigo-50 dark:bg-indigo-900/30' },
        OptionsComparison: { text: 'text-purple-600 dark:text-purple-400', border: 'border-purple-600 dark:border-purple-700', bg: 'bg-purple-50 dark:bg-purple-900/30' },
    };

    // Default tab is now 'Home'
    const [activeTab, setActiveTab] = useState('Home'); 
    const [stockTicker, setStockTicker] = useState('GOOGL');
    const [optionsTicker, setOptionsTicker] = useState('GOOGL'); // New state for options search
    const [stockAnalysis, setStockAnalysis] = useState("Search for a stock (e.g., GOOGL) to get a layman's term analysis.");
    const [optionsAnalysis, setOptionsAnalysis] = useState("Click 'Load Chain' to review the options chain for this ticker.");
    const [stockLoading, setStockLoading] = useState(false);
    const [optionsLoading, setOptionsLoading] = useState(false);
    const [userName] = useState('John Doe (JD123)'); // Mock user name

    // Portfolio State Management
    const [portfolio, setPortfolio] = useState(INITIAL_MOCK_PORTFOLIO);

    const addHolding = (newHolding) => {
        const holdingValue = newHolding.quantity * newHolding.currentPrice; 
        
        setPortfolio(prevPortfolio => ({
            ...prevPortfolio,
            holdings: [...prevPortfolio.holdings, newHolding],
            totalValue: prevPortfolio.totalValue + holdingValue,
        }));
    };


    // Function to get core stock details (unchanged)
    const fetchStockDetails = (ticker) => {
        const details = MOCK_STOCK_DETAILS[ticker] || MOCK_STOCK_DETAILS.DEFAULT;
        return details;
    };
    App.fetchStockDetails = fetchStockDetails;

    // New Function to get options chain details
    const fetchOptionsChain = (ticker) => {
        const chain = MOCK_OPTIONS_CHAINS[ticker] || MOCK_OPTIONS_CHAINS.DEFAULT;
        return chain;
    };
    App.fetchOptionsChain = fetchOptionsChain;


    // 1. Stock Analysis Handler (unchanged)
    const handleStockAnalysis = useCallback(async () => {
        if (!stockTicker) return;

        setStockLoading(true);
        setStockAnalysis("Analyzing...");
        const details = fetchStockDetails(stockTicker.toUpperCase());
        const metrics = details.overallMetrics;

        const userQuery = `Analyze the following overall metrics for the stock ${stockTicker.toUpperCase()} and provide a concise, 3-sentence summary for a retail investor: Current Price: $${metrics.price}. Volume Status: ${metrics.volumeStatus}. Volatility Status: ${metrics.volatilityStatus}. Valuation Status: ${metrics.valuationStatus}.`;

        const result = await callGeminiApi(userQuery, ['google_search']); 

        setStockAnalysis(result);
        setStockLoading(false);
    }, [stockTicker]);


    // 2. Options Analysis Handler (Updated to take the selected contract)
    const handleOptionsAnalysis = useCallback(async (selectedContract) => {
        if (!selectedContract) return;

        setOptionsLoading(true);
        setOptionsAnalysis("Generating detailed contract analysis...");

        // Construct a query using the selected contract's Greek/Value details
        const greeks = selectedContract.details.Greeks.map(g => `${g.name} (${g.value}): ${g.meaning}`).join('; ');
        const risk = selectedContract.details.RiskPerformance.map(r => `${r.name}: ${r.value}`).join('; ');
        
        const userQuery = `Provide a 3-sentence analysis for this options contract (${selectedContract.type} @ $${selectedContract.strike.toFixed(2)}): The key Greeks are: ${greeks}. The risk profile is: ${risk}. Focus on whether this is a high leverage or safe contract.`;

        const result = await callGeminiApi(userQuery);

        setOptionsAnalysis(result);
        setOptionsLoading(false);
    }, []);


    // Initial analysis on load for demo purposes
    useEffect(() => {
        handleStockAnalysis();
    }, [handleStockAnalysis]);


    // Function to render content based on active tab
    const renderContent = () => {
        switch (activeTab) {
            case 'Home':
                return <HomeTab portfolio={portfolio} addHolding={addHolding} historyData={MOCK_HISTORY_DATA} />;
            case 'StockAnalysis':
                return (
                    <StockAnalysisTab
                        stockTicker={stockTicker}
                        setStockTicker={setStockTicker}
                        stockAnalysis={stockAnalysis}
                        stockLoading={stockLoading}
                        handleStockAnalysis={handleStockAnalysis}
                    />
                );
            case 'OptionsComparison':
                return (
                    <OptionsAnalysisTab
                        optionsTicker={optionsTicker}
                        setOptionsTicker={setOptionsTicker}
                        optionsAnalysis={optionsAnalysis}
                        optionsLoading={optionsLoading}
                        handleOptionsAnalysis={handleOptionsAnalysis}
                    />
                );
            default:
                return null;
        }
    };

    const tabs = [
        { id: 'Home', label: 'Home' },
        { id: 'StockAnalysis', label: 'Stock Analysis' },
        { id: 'OptionsComparison', label: 'Options Analysis' },
    ];


    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900 font-sans p-4 sm:p-8 transition-colors duration-300">
            {/* Header / Title */}
            <header className="mb-8 p-4 bg-white dark:bg-gray-800 rounded-xl shadow-lg border-b-4 border-nexus-blue dark:border-blue-700 transition-colors duration-300">
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-extrabold text-nexus-dark dark:text-white">
                            Nexus Fin<span className="text-nexus-blue dark:text-blue-400">Analytic</span> Dashboard
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Intelligent Stock & Options Insight, powered by Nexus Analyst AI.</p>
                    </div>
                    {/* User Profile and Theme Toggle */}
                    <div className="flex items-center gap-4">
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition duration-150"
                            aria-label="Toggle dark mode"
                        >
                            {theme === 'light' ? (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9 9 0 008.354-5.646z"></path></svg> // Moon icon
                            ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg> // Sun icon
                            )}
                        </button>
                        <div className="flex items-center text-sm font-medium bg-gray-100 dark:bg-gray-700 py-2 px-3 rounded-full shadow-inner border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300">
                            <svg className="w-5 h-5 mr-2 text-nexus-blue dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                            {userName}
                        </div>
                    </div>
                </div>
            </header>

            {/* Tab Navigation Bar (Top Level - Styled Block with Background) */}
            <div className="flex bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden mb-4">
                {tabs.map((tab) => {
                    const colorMap = tabColorClasses[tab.id];
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                flex-1 py-3 px-6 text-sm font-extrabold transition duration-300 border-b-4 
                                ${activeTab === tab.id
                                    ? `${colorMap.bg} ${colorMap.text} ${colorMap.border}`
                                    : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-transparent hover:bg-gray-100 dark:hover:bg-gray-700'
                                }
                            `}
                        >
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Content Area */}
            <div className="mt-4">
                {renderContent()}
            </div>
            
            <footer className="mt-8 text-center text-xs text-gray-500 dark:text-gray-400">
                Data provided is mocked and for demonstration purposes only. Financial analysis is AI-generated.
            </footer>
        </div>
    );
}

export default App;
