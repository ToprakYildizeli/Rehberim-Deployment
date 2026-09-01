import { useContext } from 'react';
import { RoleContext } from './roleContext';

export function useRole() {
  return useContext(RoleContext);
}
