// AI 分析 mock：字段对齐 docs/API_SPEC.md 第 9 节
import type { AIAnalysisData, ApiResponse } from '../types/api'

export function mockAIAnalysis(stockCode: string): ApiResponse<AIAnalysisData> {
  return {
    code: 0,
    message: 'success',
    data: {
      stock_code: stockCode,
      quant_score: 72,
      trend: 'bullish',
      summary: `综合来看，${stockCode} 当前处于短期趋势偏强、中期震荡上行阶段。技术面动能延续，量化评分中等偏上，消息面无明显利空。整体维持谨慎乐观判断。`,
      technical_analysis:
        '价格站上 MA20 且 MA5 上穿 MA10，短期均线呈多头排列；MACD 柱状图在零轴上方温和放大；RSI14 约 62，处于强势区间但尚未超买。布林带上轨附近有压力，需关注放量突破情况。',
      quant_analysis:
        '量化综合评分 72 分（满分 100），其中趋势分 30/40、动量分 18/25、量能分 12/20、风险分 12/15。趋势与动量贡献主要得分，量能略有不足。',
      news_analysis:
        '近期无重大负面公告，行业景气度中性偏暖，市场情绪稳定。未检测到可能引发剧烈波动的突发事件。',
      advantages: [
        '短期均线多头排列，趋势结构清晰',
        'RSI 强势区间运行且未超买，上行仍有空间',
        '回撤控制良好，风险分项得分较高',
      ],
      risks: [
        '接近布林带上轨，存在技术性回调压力',
        '量能未能同步放大，突破需要成交量确认',
        '估值处于历史偏高分位，注意情绪波动',
      ],
      conclusion:
        '建议以中性偏多思路对待：持仓者可继续持有并关注 MA20 支撑，空仓者等待回调至均线附近再考虑介入，突破布林带上轨且放量时可视为趋势加强信号。',
      model_name: 'mock-model',
    },
  }
}
