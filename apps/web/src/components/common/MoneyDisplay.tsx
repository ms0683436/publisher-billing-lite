import { useMemo, memo } from "react";
import { Typography, type TypographyProps } from "@mui/material";
import { CURRENCY } from "../../constants";

interface MoneyDisplayProps extends Omit<TypographyProps, "children"> {
  value: string;
  prefix?: string;
}

// Memoized number formatter - created once per locale
const formatters = new Map<string, Intl.NumberFormat>();

function getFormatter(): Intl.NumberFormat {
  const key = CURRENCY.LOCALE;
  let formatter = formatters.get(key);
  if (!formatter) {
    formatter = new Intl.NumberFormat(CURRENCY.LOCALE, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    formatters.set(key, formatter);
  }
  return formatter;
}

export const MoneyDisplay = memo(function MoneyDisplay({
  value,
  prefix = CURRENCY.DEFAULT_PREFIX,
  ...props
}: MoneyDisplayProps) {
  const formatted = useMemo(() => {
    const numValue = parseFloat(value);
    if (Number.isNaN(numValue)) {
      return "0.00";
    }
    return getFormatter().format(numValue);
  }, [value]);

  return (
    <Typography component="span" {...props}>
      {prefix}
      {formatted}
    </Typography>
  );
});
