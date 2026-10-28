/** The part of Recharts' tooltip props our custom tooltips use; `T` is one data row of the chart. */
export interface TooltipProps<T> {
  active?: boolean
  payload?: ReadonlyArray<{ payload?: T }>
}
