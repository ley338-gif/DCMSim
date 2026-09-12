import {describe,expect,it} from 'vitest'
import {localDateString} from '../utils/dates'

describe('local DICOM date default',()=>{
 it('uses the browser calendar date rather than the UTC date',()=>{
  expect(localDateString(new Date(2026,8,12,0,30))).toBe('2026-09-12')
  expect(localDateString(new Date(2026,8,12,23,30))).toBe('2026-09-12')
 })
})
