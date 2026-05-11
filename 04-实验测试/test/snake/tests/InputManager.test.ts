import { describe, expect, it, beforeEach } from 'vitest'
import { InputManager } from '../src/input/InputManager.ts'

describe('InputManager', () => {
  let im: InputManager

  beforeEach(() => {
    im = new InputManager()
  })

  describe('enqueue', () => {
    it('正常入队：不同方向依次入队', () => {
      im.enqueue('UP')
      expect(im._getQueue()).toEqual(['UP'])
    })

    it('180° 反转拒绝：当前 RIGHT，拒绝 LEFT', () => {
      // 默认 currentDirection = RIGHT
      im.enqueue('LEFT')
      expect(im._getQueue()).toEqual([])
    })

    it('180° 反转拒绝：当前 UP，拒绝 DOWN', () => {
      im.enqueue('UP')
      im.consume() // currentDirection = UP
      im.enqueue('DOWN')
      expect(im._getQueue()).toEqual([])
    })

    it('180° 反转基于队尾：队列=[UP]，拒绝 DOWN', () => {
      im.enqueue('UP')
      im.enqueue('DOWN') // 基于队尾 UP，DOWN 被拒绝
      expect(im._getQueue()).toEqual(['UP'])
    })

    it('队列上限：超过 2 个方向时丢弃', () => {
      im.enqueue('UP')
      im.enqueue('LEFT')
      im.enqueue('DOWN') // 第 3 个，被丢弃
      expect(im._getQueue()).toEqual(['UP', 'LEFT'])
    })

    it('相同方向可以入队（非 180°）', () => {
      im.enqueue('UP')
      im.consume()
      im.enqueue('UP')
      expect(im._getQueue()).toEqual(['UP'])
    })
  })

  describe('consume', () => {
    it('队列有值：返回队首并移除', () => {
      im.enqueue('UP')
      im.enqueue('LEFT')
      expect(im.consume()).toBe('UP')
      expect(im._getQueue()).toEqual(['LEFT'])
    })

    it('队列为空：返回 null', () => {
      expect(im.consume()).toBeNull()
    })

    it('consume 更新 currentDirection：影响下次防反转检查', () => {
      im.enqueue('UP')
      im.consume() // currentDirection = UP
      im.enqueue('DOWN') // 应被拒绝
      expect(im._getQueue()).toEqual([])
    })
  })

  describe('reset', () => {
    it('清空队列并重置方向', () => {
      im.enqueue('UP')
      im.reset('LEFT')
      expect(im._getQueue()).toEqual([])
      // 重置后 currentDirection = LEFT，尝试入队 UP（合法，非 180°）
      im.enqueue('UP')
      expect(im._getQueue()).toEqual(['UP'])
    })

    it('reset 后 180° 检查基于新方向', () => {
      im.reset('UP')
      im.enqueue('DOWN') // 相对 UP 是 180°，应被拒绝
      expect(im._getQueue()).toEqual([])
    })
  })

  describe('快速连按场景', () => {
    it('RIGHT → UP → LEFT：依次消费，每次正确防反转', () => {
      // currentDirection = RIGHT
      im.enqueue('UP')    // OK，队列=[UP]
      im.enqueue('LEFT')  // 基于队尾 UP，LEFT 合法，队列=[UP,LEFT]
      expect(im._getQueue()).toEqual(['UP', 'LEFT'])

      expect(im.consume()).toBe('UP')   // currentDir=UP，队列=[LEFT]
      expect(im.consume()).toBe('LEFT') // currentDir=LEFT，队列=[]
      expect(im.consume()).toBeNull()
    })

    it('RIGHT → DOWN → UP：DOWN 合法，UP 被拒绝（基于队尾 DOWN）', () => {
      im.enqueue('DOWN') // OK，队列=[DOWN]
      im.enqueue('UP')   // 基于队尾 DOWN，UP 是 180°，被拒绝
      expect(im._getQueue()).toEqual(['DOWN'])
    })
  })
})
