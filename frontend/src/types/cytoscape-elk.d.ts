/**
 * Type declarations for cytoscape-elk module.
 */

declare module 'cytoscape-elk' {
  import cytoscape from 'cytoscape';
  
  function elk(cytoscape: typeof import('cytoscape')): void;
  export default elk;
}

