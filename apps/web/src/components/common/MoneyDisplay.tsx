import { Typography, type TypographyProps } from "@mui/material";

interface MoneyDisplayProps extends Omit<TypographyProps, "children"> {
  value: string;
  prefix?: string;
}

export function MoneyDisplay({
  value,
  prefix = "$",
  ...props
}: MoneyDisplayProps) {
  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parseFloat(value));

  return (
    <Typography component="span" {...props}>
      {prefix}
      {formatted}
    </Typography>
  );
}
