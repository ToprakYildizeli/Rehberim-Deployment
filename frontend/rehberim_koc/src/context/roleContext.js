import { createContext } from 'react';

/** Kept separate from the provider so fast refresh stays happy. */
export const RoleContext = createContext(null);
