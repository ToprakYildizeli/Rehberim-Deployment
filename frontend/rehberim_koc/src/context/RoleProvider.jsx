import { useEffect, useMemo, useState } from 'react';
import { RoleContext } from './roleContext';

export function RoleProvider({ children }) {
  const [role, setRole] = useState(() => localStorage.getItem('role') || 'ogretmen');

  useEffect(() => {
    localStorage.setItem('role', role);
  }, [role]);

  const value = useMemo(() => ({ role, setRole }), [role]);

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}
