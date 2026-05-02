interface ClaimRowActionsProps {
  claimId: string;
  onVerify: (id: string) => void;
  onChallenge: (id: string) => void;
  onSupplement: (id: string) => void;
  onDismiss: (id: string) => void;
}

export function ClaimRowActions({
  claimId,
  onVerify,
  onChallenge,
  onSupplement,
  onDismiss,
}: ClaimRowActionsProps) {
  return (
    <div style={{ display: "flex", gap: "4px" }}>
      <button onClick={() => onVerify(claimId)}>Verify</button>
      <button onClick={() => onChallenge(claimId)}>Challenge</button>
      <button onClick={() => onSupplement(claimId)}>Supplement</button>
      <button onClick={() => onDismiss(claimId)}>Dismiss</button>
    </div>
  );
}
