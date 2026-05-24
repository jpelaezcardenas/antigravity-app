export function calculateWithdrawalImpact(amount: number, cashWithoutWithdrawal: number) {
  const remainingCash = cashWithoutWithdrawal - amount;
  return {
    remainingCash,
    isHealthy: remainingCash >= (cashWithoutWithdrawal * 0.2), // Minimum safe threshold
    message: remainingCash >= (cashWithoutWithdrawal * 0.2) 
      ? "Nivel de caja seguro posterior al retiro."
      : "Riesgo de liquidez: la caja queda por debajo del umbral recomendado."
  };
}
